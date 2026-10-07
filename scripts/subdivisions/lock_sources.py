#!/usr/bin/env python3
"""Pin the Wikimedia Commons revision, license and author of every recipe in flags.json.

Writes sources.json. For each flag it records the Commons file, the SHA-1 of
the revision the committed artwork was built from, the license the drawing
can be redistributed under with every license tag it was worked out from,
the author as the file page names them, the files the drawing was built
from with their own authors and licenses, and the English Wikipedia article
for the subdivision (looked up on Wikidata through its ISO 3166-2 code,
property P300).

Existing pins are kept: re-running this script never moves a flag to a newer
upload by itself. Pass --refresh CODE... to re-pin specific flags after their
new artwork has been reviewed. Licenses and authors are read again on every
run, since they belong to the file page rather than to a revision.

The Author field of a file page usually describes the first upload, while
the pinned revision may have been redrawn by others since. So the script
also reads the file's upload history and records the uploads the pinned
revision descends from (a re-upload of earlier bytes, a revert, continues
from those bytes). Credits name everyone in that ancestry whom the Author
field does not already name. When the flag's public-domain status rests on
one person's release and others contributed to the pinned drawing, see
commons_license.py: a public license on the page takes over, and if there
is none the recipe has to say under "later_versions" what the other uploads
changed, after a look at the file history.

License policy: the license never decides whether a flag is included, only
how it is credited. Public-domain and CC0 artwork needs no credit; anything
that asks for attribution (CC BY, CC BY-SA, an author's own attribution
terms) gets a credit that render_docs.py writes into the README, and
share-alike files are distributed under their CC BY-SA license instead of
MIT. See commons_license.py for how the license is worked out.

The script stops instead of writing sources.json when a file has no
license tag, when its share-alike licenses cannot be combined, when its
page names no author (or the author text reads like license boilerplate),
or when a release by one person would have to cover other people's uploads
and the recipe has no "later_versions" note, since none of those can be
credited correctly.

Usage: lock_sources.py [--refresh CODE...]
"""

import argparse
import json
import re
import sys
import urllib.parse

from commons_author import looks_like_license
from commons_license import Resolver
from common import SOURCES_JSON, http_get, load_flags, write_json, select_codes

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
KIND_NAMES = {"design": "public domain", "release": "public domain", "attribution": "attribution",
              "copyleft": "share-alike"}


def commons_info(titles):
    """Return {title: page} for each file, with its whole upload history
    (newest first) under "imageinfo"."""
    info = {}
    for title in sorted(set(titles)):
        # The history of one file per request: iilimit applies to the whole
        # query, so batching files would cut their histories short.
        query = urllib.parse.urlencode({
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|sha1|timestamp|size|user|comment",
            "iilimit": "max",
            "titles": "File:" + title,
        })
        page = json.loads(http_get(f"{COMMONS_API}?{query}"))["query"]["pages"][0]
        if page.get("missing") or "imageinfo" not in page:
            sys.exit(f"Commons has no file named {title!r}")
        info[title] = page
    return info


def lineage(uploads, sha1):
    """The uploads a revision descends from, oldest first.

    Each upload is taken to build on the bytes before it, except that
    re-uploading bytes that were there before (a revert) goes back to the
    ancestry of those bytes.
    """
    ancestry, current = {}, None
    for upload in reversed(uploads):
        if upload["sha1"] not in ancestry:
            ancestry[upload["sha1"]] = (ancestry[current] if current else []) + [upload]
        current = upload["sha1"]
    return ancestry.get(sha1, [])


def version_record(upload):
    comment = (upload.get("comment") or "").strip().splitlines()
    return {"user": upload["user"], "date": upload["timestamp"][:10],
            "comment": comment[0][:160] if comment else ""}


def named_in(user, text):
    """Whether an author text already names a Commons user."""
    return re.sub(r"~commonswiki$", "", user).lower() in (text or "").lower()


def wikidata_lookup(codes):
    """Return {code: {wikidata, wikipedia, flags}} for ISO 3166-2 codes.

    Wikidata sometimes gives a subdivision's ISO code to something inside it
    as well (a national park, a former entity), so when several items carry
    the code, the one with a flag image wins, then the one with the most
    sitelinks.
    """
    values = " ".join(f'"{c.upper()}"' for c in codes)
    sparql = f"""
SELECT ?iso ?item ?article ?flag ?links WHERE {{
  VALUES ?iso {{ {values} }}
  ?item p:P300 ?isoStatement .
  ?isoStatement ps:P300 ?iso ; wikibase:rank ?isoRank .
  FILTER(?isoRank != wikibase:DeprecatedRank)
  ?item wikibase:sitelinks ?links .
  OPTIONAL {{ ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }}
  OPTIONAL {{ ?item wdt:P41 ?flag . }}
}}"""
    url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({"query": sparql, "format": "json"})
    rows = json.loads(http_get(url))["results"]["bindings"]
    items = {}
    for row in rows:
        code = row["iso"]["value"].lower()
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        record = items.setdefault(code, {}).setdefault(qid, {"wikidata": qid, "wikipedia": None, "flags": set(),
                                                             "links": int(row["links"]["value"])})
        if "article" in row:
            record["wikipedia"] = urllib.parse.unquote(row["article"]["value"].rsplit("/wiki/", 1)[-1])
        if "flag" in row:
            record["flags"].add(urllib.parse.unquote(row["flag"]["value"].rsplit("/", 1)[-1]).replace("_", " "))
    return {code: max(candidates.values(), key=lambda r: (bool(r["flags"]), r["links"]))
            for code, candidates in items.items()}


def license_url(label):
    """The deed or terms page of a license label, or None for public domain."""
    m = re.match(r"CC BY(-SA)? (\d\.\d)(?: ([A-Z]{2}))?$", label)
    if m:
        port = f"{m.group(3).lower()}/" if m.group(3) else ""
        return f"https://creativecommons.org/licenses/by{'-sa' if m.group(1) else ''}/{m.group(2)}/{port}"
    if label == "Copyrighted free use":
        return "https://commons.wikimedia.org/wiki/Template:Copyrighted_free_use"
    if label == "CC0":
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    if label == "GFDL":
        return "https://www.gnu.org/licenses/fdl-1.3.html"
    m = re.match(r"attribution requested by \{\{(User:[^}]+)\}\}$", label)
    if m:
        return "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(m.group(1).replace(" ", "_"), safe=":/")
    return None


def license_name(label):
    """How a license label reads in a credit."""
    if label.startswith("attribution requested by "):
        return "attribution as the author requests"
    return label


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", nargs="*", default=[], metavar="CODE",
                        help="re-pin these flags to the current Commons revision")
    parser.add_argument("codes", nargs="*", help="only update these codes or country prefixes")
    args = parser.parse_args()

    all_flags = load_flags()["flags"]
    flags = {c: all_flags[c] for c in select_codes(args.codes, all_flags)}
    existing = json.loads(SOURCES_JSON.read_text(encoding="utf-8")) if SOURCES_JSON.exists() else {}

    info = commons_info(recipe["commons"] for recipe in flags.values())
    wikidata = wikidata_lookup(flags)
    resolver = Resolver()
    resolver.prefetch(recipe["commons"] for recipe in flags.values())

    problems = []
    out = dict(existing)
    for code in sorted(flags):
        recipe = flags[code]
        title = recipe["commons"]
        uploads = info[title]["imageinfo"]
        current = uploads[0]
        pinned = existing.get(code)
        keep_pin = pinned and pinned["commons_title"] == title and code not in args.refresh
        revision = pinned["revision"] if keep_pin else {
            "sha1": current["sha1"],
            "timestamp": current["timestamp"],
            "url": current["url"],
            "width": current["width"],
            "height": current["height"],
        }
        versions = lineage(uploads, revision["sha1"])
        if not versions:
            problems.append(f"{code}: the pinned revision {revision['sha1']} is not in the upload history of {title!r}")
            continue
        revision = {key: value for key, value in revision.items() if key != "uploader"}
        revision["uploader"] = versions[-1]["user"]

        terms = resolver.resolve(title, versions=versions)
        if terms["kind"] == "unknown":
            problems.append(f"{code}: {title!r} has no usable license ({terms['license']}; "
                            f"tags: {', '.join(terms['tags']) or 'none'})")
        if terms["license"] == "GFDL":
            problems.append(f"{code}: {title!r} is offered only under the GFDL, whose full text would have to "
                            f"ship with the flag; look for a CC BY-SA alternative on the page or another drawing")
        author = terms["author"]
        if not author or looks_like_license(author):
            problems.append(f"{code}: the page of {title!r} names no author, or its Author field reads like "
                            f"license text ({author!r})")
        credited = [part for part in terms["components"] if part["binding"]]
        for part in credited:
            if not part["author"] or looks_like_license(part["author"]):
                problems.append(f"{code}: {part['title']!r}, which {title!r} is built from, names no author")
        if terms["outsiders"] and not recipe.get("later_versions"):
            problems.append(f"{code}: {title!r} is public domain by {terms['releaser']}'s release, but the pinned "
                            f"revision also has uploads by {', '.join(terms['outsiders'])}; check the file history "
                            f"and say in the recipe's \"later_versions\" what they changed")

        wd = wikidata.get(code, {})
        if recipe.get("wikipedia"):
            wd["wikipedia"] = recipe["wikipedia"]
        if not wd.get("wikipedia"):
            problems.append(f"{code}: Wikidata has no English Wikipedia article for ISO code {code.upper()}")
        out[code] = {
            "commons_title": title,
            "commons_page": current["descriptionurl"],
            "revision": revision,
            # What the drawing, with everything it was built from, can be
            # redistributed under; this decides the credit.
            "license": license_name(terms["license"]),
            "license_kind": KIND_NAMES.get(terms["kind"], terms["kind"]),
            "license_url": license_url(terms["license"]),
            # The audit trail: the page's license categories, the licenses it
            # offers and the attribution requests it makes.
            "license_tags": terms["tags"],
            "license_options": terms["options"],
            "license_conditions": terms["conditions"],
            "own_license": license_name(terms["own_license"]),
            "own_license_url": license_url(terms["own_license"]),
            # design: a public-domain claim about the flag or arms only;
            # release: the drawer's own public-domain release or CC0;
            # attribution or copyleft: the license the drawer chose.
            "own_kind": terms["own_kind"],
            "author": author,
            # The uploads the pinned revision descends from, and those of
            # their uploaders whom the Author field does not name; credits
            # name them too.
            "versions": [version_record(v) for v in versions],
            "contributors": list(dict.fromkeys(v["user"] for v in versions if not named_in(v["user"], author))),
            # Who released the drawing into the public domain, when it rests
            # on a release, and how the uploads by others were reviewed.
            "releaser": terms["releaser"],
            "release_not_used": (f"{terms['releaser']}'s public-domain release covers only their own work, and "
                                 f"the pinned revision has uploads by others too, so the page's "
                                 f"{terms['own_license']} applies" if terms["release_limited"] else None),
            "later_versions": recipe.get("later_versions") if terms["outsiders"] else None,
            "derived_from": [{
                "title": part["title"],
                "page": part["page"],
                "author": part["author"],
                "license": license_name(part["license"]),
                "license_url": license_url(part["license"]),
                # Whether this file's license holds for the flag too (see
                # commons_license.py); sources that do not are recorded only.
                "binding": part["binding"],
            } for part in terms["components"]],
            "attribution_required": terms["kind"] in ("attribution", "copyleft"),
            "wikidata": wd.get("wikidata"),
            "wikipedia": wd.get("wikipedia"),
            # Recorded so a reviewer can see where the chosen artwork differs
            # from the flag image Wikidata currently lists for the region.
            "wikidata_flag_images": sorted(wd.get("flags", [])),
        }
        if keep_pin and pinned["revision"]["sha1"] != current["sha1"]:
            print(f"note: {code}: Commons has a newer upload of {title!r}; keeping the pinned revision "
                  f"(re-pin with --refresh {code} after reviewing it)")

    if problems:
        sys.exit("\n".join(problems))
    write_json(SOURCES_JSON, out)
    print(f"pinned {len(out)} flags in {SOURCES_JSON.name}")


if __name__ == "__main__":
    main()
