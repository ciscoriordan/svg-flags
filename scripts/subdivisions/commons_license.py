"""Work out which license a Wikimedia Commons file can be redistributed under.

Commons reports one license per file (extmetadata LicenseShortName), and for
a file with several license tags that is simply the first tag. Flag files
often carry a public-domain tag for the design (the flag or coat of arms is
an official symbol) next to the license the person who drew the SVG chose
for the drawing, so that field can say "Public domain" for a drawing that is
GFDL or CC BY. This module reads every tag instead:

  - The license categories of the page. License templates, including ones
    hidden inside user templates, add these, so they are the most complete
    machine-readable record.
  - The {{self}}, {{self2}} and {{GFDL-self}} templates in the wikitext,
    which name licenses that add no category of their own (the CC BY-SA
    3.0 that {{GFDL-self|migration=relicense}} grants, for example).
  - User templates that ask for attribution in prose (for example
    {{User:Heraldry/Attribution}}), which add no license category.
  - The files the drawing was built from: {{Attrib}}, {{AttribSVG}},
    {{Own based}}, {{Derived from}} and {{Extracted from}}, and files linked
    from the Source field. Their licenses bind the derived drawing too.

Every tag falls into one of four kinds:

  design       a public-domain claim about the design itself (PD-BrazilGov,
               PD-Coa-Mexico, PD-old-70, PD-ineligible, ...). It does not
               license the drawing, so on its own it does not decide.
  release      the drawer gave up their rights (PD-self, PD-user, CC0).
  attribution  free to reuse with credit (CC BY, attribution requests).
  copyleft     share-alike (CC BY-SA, GFDL, Free Art License).

The licenses on a file page are alternatives: Commons treats a file with
several license tags as multi-licensed, and a reuser may pick any of them
(Commons:Multi-licensing). The pick is the most permissive one, and among
equally permissive ones a Creative Commons license over the GFDL (a CC
license asks for a credit and a link, while the GFDL asks for its full text
to travel with every copy), then the newest version. Design-level tags are
not alternatives, since they do not license the drawing; they decide only
when nothing else is tagged. Attribution requests in user templates are
conditions on top of whichever license is picked.

The files a drawing was built from are cumulative instead: their licenses
hold at the same time as the drawing's own, so the most restrictive one
governs. Two exceptions: a file tagged as too simple for copyright
(PD-ineligible, PD-shape) cannot have taken protected expression from the
files it was built from, and an author who released a drawing into the
public domain also released the parts of it that were their own earlier
work. Those sources are recorded but do not bind the drawing.

A public-domain release or CC0 dedication by a person ({{PD-self}},
{{PD-user|Name}}, {{PD-author|Name}}, {{self|cc-zero}}) covers that
person's own work and nothing else. Commons files are often overwritten by
other users later, so the caller passes the uploads the pinned revision
descends from: when someone other than the releaser contributed to it, the
release cannot be relied on for the whole drawing. If the page also offers
a public license (CC BY, CC BY-SA), which any uploader publishes a new
version under, that license is used instead and everyone who contributed is
credited. If it offers nothing else, the result lists those uploaders as
"outsiders", and lock_sources.py asks for a reviewed note on what their
uploads changed.

A file with no license tag at all is "unknown", which the pipeline refuses.

The result names the license the drawing can be redistributed under, its
author's own terms, and every file it was built from with that file's
author and license, which is what a credit has to name.
"""

import json
import re
import urllib.parse

from commons_author import AuthorReader, author_of, release_author, split_top_level
from common import http_get

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
RANK = {"design": 0, "release": 0, "attribution": 1, "copyleft": 2, "unknown": 3}
SELF_TEMPLATE = re.compile(r"\{\{\s*([Ss]elf2?|GFDL-self[^|{}]*)\s*((?:\|[^{}]*)?)\}\}")
COMPONENT_TEMPLATE = re.compile(
    r"\{\{\s*(?:[Aa]ttrib(?:SVG)?|[Oo]wn based|[Dd]erived from|[Ee]xtracted from|[Ii]mage extracted)\s*\|\s*"
    r"(?:1\s*=\s*)?([^|{}]+?)\s*[|}]")
FILE_LINK = re.compile(r"\[\[\s*:?\s*(?:File|Image)\s*:\s*([^\]|]+?)\s*[\]|]", re.I)
F_TEMPLATE = re.compile(r"\{\{\s*F\s*\|\s*([^|{}]+?)\s*[|}]")
USER_TEMPLATE = re.compile(r"\{\{\s*(User:[^|{}]+?)\s*[|}]")
SOURCE_FIELD = re.compile(r"(?ims)^\s*\|\s*source\s*=(.*?)(?=^\s*\||^\s*\}\})")
CC_TAG = re.compile(r"cc-by(-sa)?-(\d\.\d)(?:-([a-z]{2}))?(?![a-z])")


def page_url(title):
    return "https://commons.wikimedia.org/wiki/" + urllib.parse.quote("File:" + title.replace(" ", "_"), safe=":/(),")


def tag_kind(name):
    """Classify a license template or license category name.

    Returns (kind, label), or None when the name is not a license at all
    ("Self-published work", "License migration completed", ...). Creative
    Commons labels keep the version and any jurisdiction port ("CC BY 2.5
    AR"), since each port has its own legal code.
    """
    n = name.strip().lower().replace("_", " ")
    if "missing sdc" in n or n.startswith(("license migration", "self-published")):
        return None
    # {{cc-by-sa-all}} offers every version from 1.0 to 4.0.
    n = re.sub(r"^cc-by(-sa)?-all\b", lambda m: f"cc-by{m.group(1) or ''}-4.0", n)
    m = CC_TAG.match(n)
    if m:
        port = f" {m.group(3).upper()}" if m.group(3) else ""
        if m.group(1):
            return "copyleft", f"CC BY-SA {m.group(2)}{port}"
        return "attribution", f"CC BY {m.group(2)}{port}"
    if n.startswith("gfdl"):
        return "copyleft", "GFDL"
    if n.startswith(("fal", "free art license")):
        return "copyleft", "Free Art License"
    if n in ("cc-zero", "cc0", "cc-0"):
        return "release", "CC0"
    if re.match(r"pd-(self|user|author|release)\b", n):
        return "release", "Public domain"
    if n.startswith(("pd-", "pd ", "cc-pd-mark")) or "public domain" in n:
        return "design", "Public domain"
    if n == "copyrighted free use":
        return "attribution", "Copyrighted free use"
    if n.startswith("attribution"):
        return "attribution", "Attribution"
    return None


def preference(option):
    """Sort key among options of the same kind: lower is preferred."""
    kind, label = option
    m = re.match(r"CC BY(?:-SA)? (\d\.\d)( [A-Z]{2})?$", label)
    if m:
        # Newest version first; the international license before a port.
        return (0, -float(m.group(1)), 1 if m.group(2) else 0)
    return (1, 0, 0)


def most_permissive(options):
    """The option a reuser would pick from one requirement."""
    best = min(RANK[kind] for kind, _ in options)
    return min((o for o in options if RANK[o[0]] == best), key=preference)


def most_restrictive(requirements):
    """The terms that satisfy every requirement at once."""
    worst = max(RANK[kind] for kind, _ in requirements)
    candidates = [o for o in requirements if RANK[o[0]] == worst]
    if worst == RANK["copyleft"]:
        labels = {label for _, label in candidates}
        # Every CC BY-SA license lets an adaptation use a later version, so
        # the newest one present satisfies all of them; the GFDL and the
        # Free Art License have no such bridge.
        if len(labels) > 1 and not all(label.startswith("CC BY-SA") for label in labels):
            return "unknown", "incompatible share-alike licenses: " + " and ".join(sorted(labels))
        return min(candidates, key=preference)
    return candidates[0]


def fetch_pages(titles):
    """Return {title: {"wikitext", "categories", "missing"}} for the given pages."""
    pages = {}
    titles = sorted(set(titles))
    for start in range(0, len(titles), 20):
        batch = titles[start:start + 20]
        query = {
            "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
            "prop": "revisions|categories", "rvprop": "content", "rvslots": "main",
            "cllimit": "max", "titles": "|".join(batch),
        }
        while True:
            response = json.loads(http_get(f"{COMMONS_API}?{urllib.parse.urlencode(query)}"))
            data = response["query"]
            # Report each page under the title that was asked for, even when
            # Commons normalized it or followed a redirect.
            back = {t: t for t in batch}
            for step in data.get("normalized", []) + data.get("redirects", []):
                back[step["to"]] = back.get(step["from"], step["from"])
            for page in data["pages"]:
                record = pages.setdefault(back.get(page["title"], page["title"]),
                                          {"wikitext": None, "categories": [], "missing": False})
                record["missing"] = bool(page.get("missing"))
                if page.get("revisions"):
                    record["wikitext"] = page["revisions"][0]["slots"]["main"]["content"]
                record["categories"] += [c["title"].split(":", 1)[1] for c in page.get("categories", [])]
            if "continue" not in response:
                break
            query.update(response["continue"])
    return pages


def self_options(wikitext):
    """The license alternatives of each {{self}}-style template."""
    sets = []
    for name, raw in SELF_TEMPLATE.findall(wikitext or ""):
        args = [a.strip() for a in split_top_level(raw)[1:]]
        options = [tag_kind(a) for a in args if a and "=" not in a]
        # A public-domain claim about the design ({{self2|PD-BrazilGov|
        # cc-by-2.5}}) is not something the drawer can grant; the drawing is
        # offered under the remaining licenses.
        options = [o for o in options if not (o and o[0] == "design")]
        if name.lower().startswith("gfdl-self"):
            options.append(("copyleft", "GFDL"))
            if re.search(r"migration\s*=\s*relicense", raw):
                options.append(("copyleft", "CC BY-SA 3.0"))
        options = [o if o else ("unknown", "unrecognized license template") for o in options]
        if options:
            sets.append(options)
    return sets


def components(wikitext):
    """Files the drawing was built from, as its page names them."""
    found = [m.strip() for m in COMPONENT_TEMPLATE.findall(wikitext or "")]
    for field in SOURCE_FIELD.findall(wikitext or ""):
        found += [m.strip() for m in FILE_LINK.findall(field)]
        found += [m.strip() for m in F_TEMPLATE.findall(field)]
    titles = []
    for title in found:
        title = urllib.parse.unquote(title).replace("_", " ").strip()
        title = re.sub(r"^(File|Image):", "", title, flags=re.I)
        if title and title not in titles:
            titles.append(title)
    return titles


def same_person(a, b):
    """Whether two author strings name the same single person."""
    def norm(name):
        return re.sub(r"\s*\(uploader\)$", "", name or "").strip().lower()
    return bool(norm(a)) and norm(a) == norm(b)


def user_key(user):
    """A Commons user name compared without case or the suffix that the 2015
    account unification added to some names ("Name~commonswiki")."""
    return re.sub(r"~commonswiki$", "", user or "").strip().lower()


def releasers_of(wikitext, author, versions):
    """Who released a drawing, and whether the release names them.

    {{PD-user|Name}}, {{PD-author|Name}} and the like name the person. A
    {{PD-self}} or {{self|cc-zero}} without a name speaks for whoever added
    it, which is the uploader the Author field names, or else the first
    uploader.
    """
    named = release_author(wikitext)
    if named:
        return [named], True
    uploaders = list(dict.fromkeys(v["user"] for v in versions or ()))
    in_author = [u for u in uploaders if user_key(u) and user_key(u) in (author or "").lower()]
    return in_author or uploaders[:1], False


def outsiders_of(versions, releasers, named):
    """Uploaders of the pinned drawing's ancestry who are not a releaser.

    versions are the uploads the pinned revision descends from, oldest
    first. When the release names someone who did not upload the file
    ({{PD-author|James Leigh}} uploaded by Kooma, {{PD-OpenClipart}}), the
    first upload is taken to be that person's work.
    """
    if not versions:
        return []
    exempt = {user_key(r) for r in releasers}
    if named and user_key(versions[0]["user"]) not in exempt:
        exempt.add(user_key(versions[0]["user"]))
    found = []
    for version in versions:
        if user_key(version["user"]) not in exempt and version["user"] not in found:
            found.append(version["user"])
    return found


class Resolver:
    """Resolves the license and author of Commons files, with caching."""

    def __init__(self):
        self.pages = {}
        self.user_templates = {}
        self.results = {}
        self.authors = AuthorReader()

    def prefetch(self, titles):
        wanted = ["File:" + t for t in titles if "File:" + t not in self.pages]
        if wanted:
            self.pages.update(fetch_pages(wanted))

    def user_templates_of(self, wikitext):
        """(offers, conditions) from the user templates a page uses.

        A user template that wraps a {{self}} license offers those licenses;
        one that asks for credit in prose without a license template adds
        that as a condition on reuse.
        """
        names = sorted(set(USER_TEMPLATE.findall(wikitext or "")))
        missing = [n for n in names if n not in self.user_templates]
        if missing:
            for name, record in fetch_pages(missing).items():
                self.user_templates[name] = record["wikitext"] or ""
        offers, conditions = [], []
        for name in names:
            text = self.user_templates.get(name, "")
            offers += [option for options in self_options(text) for option in options]
            if re.search(r"\battribut", text, re.I) and not SELF_TEMPLATE.search(text):
                conditions.append(("attribution", f"attribution requested by {{{{{name}}}}}"))
        return offers, conditions

    def resolve(self, title, depth=0, seen=(), versions=None):
        """Return the terms of a file.

        versions, for the pinned file itself, are the uploads its pinned
        revision descends from (oldest first, each {"user", ...}); they
        decide whether a personal release covers the whole drawing.

        {"license", "kind"}: what the drawing, with everything it was built
            from, can be redistributed under.
        {"own_license", "own_kind"}: the terms its author chose for this
            file alone.
        "options": the licenses the page offers, and "conditions" the
            attribution requests, for the audit trail; "tags": the page's
            license categories.
        "author": the author as the page names them (None if it names none).
        "components": the files it was built from, each with its own terms,
            author and whether its license binds this file.
        """
        key = (title, tuple(v["user"] for v in versions or ()))
        if key in self.results:
            return self.results[key]
        self.prefetch([title])
        page = self.pages.get("File:" + title)
        if page is None or page["missing"]:
            return {"license": "file not found", "kind": "unknown", "own_license": "file not found",
                    "own_kind": "unknown", "options": [], "conditions": [], "tags": [], "author": None,
                    "components": [], "releaser": None, "outsiders": [], "release_limited": False}
        wikitext = page["wikitext"] or ""
        offers = [option for options in self_options(wikitext) for option in options]
        user_offers, conditions = self.user_templates_of(wikitext)
        offers += user_offers
        tags = []
        # Some current license templates have no category yet. Inspect their
        # explicit names too, without treating design tags as artwork releases.
        templates = re.findall(r"\{\{\s*([^{}|]+)", wikitext)
        for category in sorted(set(page["categories"]) | {n.strip() for n in templates if tag_kind(n)}):
            kind = tag_kind(category)
            if kind is None:
                continue
            tags.append(category)
            if kind[0] != "design":
                offers.append(kind)
        offers = list(dict.fromkeys(offers))
        has_design = any(tag_kind(t)[0] == "design" for t in tags)
        # A file tagged as too simple for copyright cannot have taken any
        # protected expression from the files it was built from.
        ineligible = any(re.search(r"pd[ -](ineligible|shape|textlogo|simple)", t, re.I) for t in tags)

        if offers:
            own = most_permissive(offers)
        elif has_design:
            own = ("design", "Public domain")
        else:
            own = ("unknown", "no license tag")

        author = author_of(title, wikitext, self.authors)

        # A release covers the releaser's own work. If others uploaded parts
        # of the pinned drawing, a public license on the page (which they
        # published their versions under) takes over where there is one.
        releaser, outsiders, release_limited = None, [], False
        if own[0] == "release":
            releasers, named = releasers_of(wikitext, author, versions)
            releasers = [self.authors.text(r) for r in releasers]
            releaser = ", ".join(releasers) or None
            outsiders = outsiders_of(versions, releasers, named)
            public = [o for o in offers if o[0] in ("attribution", "copyleft")]
            if outsiders and public:
                own = most_permissive(public)
                release_limited = True

        if conditions and own[0] != "unknown":
            own = most_restrictive([own] + conditions)
        governing = [own]
        parts = []
        if depth < 3:
            names = [c for c in components(wikitext) if c != title and c not in seen]
            self.prefetch(names)
            for name in names:
                sub = self.resolve(name, depth + 1, seen + (title,))
                # A reference image that has since been deleted from Commons
                # cannot be checked; it is recorded but does not decide.
                own_work = own[0] == "release" and same_person(author, sub["author"])
                binding = (sub["license"] != "file not found" and not ineligible and not own_work
                           and sub["kind"] not in ("design", "release"))
                parts.append({"title": name, "page": page_url(name), "license": sub["license"],
                              "kind": sub["kind"], "author": sub["author"], "binding": binding})
                if binding:
                    governing.append((sub["kind"], sub["license"]))
        kind, label = most_restrictive(governing)

        def plain(option):
            kind, label = option
            return kind, "Public domain" if kind in ("design", "release") and label != "CC0" else label

        own_kind, own_label = plain(own)
        kind, label = plain((kind, label))
        result = {
            "license": label, "kind": kind, "own_license": own_label, "own_kind": own_kind,
            "options": [label for _, label in offers], "conditions": [label for _, label in conditions],
            "tags": tags, "author": author, "components": parts,
            "releaser": releaser, "outsiders": [] if release_limited else outsiders,
            "release_limited": release_limited,
        }
        self.results[key] = result
        return result
