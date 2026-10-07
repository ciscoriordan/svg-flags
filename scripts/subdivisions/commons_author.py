"""Read the author of a Wikimedia Commons file from its wikitext.

Commons' own metadata (extmetadata "Artist") is the rendered HTML of the
file page's Author field, and when that field is missing or holds a license
template, it picks up whatever the page renders there instead: license
boxes ("This work has been released into the public domain by its
author..."), or nothing at all. Credits need the name the page actually
gives, so this module reads the wikitext:

  1. The Author parameter of the description template ({{Information}},
     {{Artwork}} and the like).
  2. If that is missing, empty, or only says "own work" or "see file
     history", the author named in a public-domain release or a {{self}}
     license: {{PD-user|Name}}, {{PD-self|author=Name}},
     {{self|...|author=Name}}, or the Open Clip Art Library for
     {{PD-OpenClipart}}.
  3. Failing that, the user who first uploaded the file, which is who
     {{PD-self}} and {{self}} without a name refer to.

The wikitext is turned into plain text by expanding the handful of
templates file pages use for names (user links, {{AutVec}}, {{Creator}},
{{Unknown|author}}, ...). Notices that are not names (license tags,
{{Insignia}}, {{Inkscape}}) are dropped. Any other template is rendered by
the Commons parser and reduced to its text.

author_of() returns None when no author can be found, and looks_like_license()
flags text that is license boilerplate rather than a name; lock_sources.py
refuses both.
"""

import html
import json
import re
import urllib.parse

from common import http_get

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

DESCRIPTION_TEMPLATES = {"information", "artwork", "photograph", "art photo", "map", "book"}
USER_LINK_TEMPLATES = {"u", "user", "ut", "uc", "u2", "user2", "ul", "userlink", "user link", "user5", "ud"}
# Templates that mark how a file was made or what it shows, not who made it.
NOTICE_TEMPLATES = {
    "insignia", "inkscape", "created with inkscape", "igen", "image generation", "easy-border", "validsvg",
    "simplsvg", "trademarked", "allow overwriting", "please-do-not-overwrite-permanent-version", "convert to svg",
    "superseded", "fictitious flag", "cleanup", "tbc", "colorbox", "flagcolors", "includes coat of arms",
    "graphic lab", "using", "based", "attrib", "attribsvg", "own based", "derived from", "extracted from",
    "thv",
}
NOT_AN_AUTHOR = {"own", "own work", "own assumed", "self-made", "self-photographed", "see file history",
                 "see history", "see below"}
LICENSE_TEXT = re.compile(
    r"public domain|licen[cs]|copyright|creative commons|\bcc[- ]?(by|0|zero)\b|\bgfdl\b|released into|"
    r"this (work|file|image)\b|free to (share|use|copy)|permission is granted|attribut", re.I)


def looks_like_license(text):
    return bool(LICENSE_TEXT.search(text or ""))


# ------------------------------------------------------------- wikitext parse

def split_top_level(text, separator="|"):
    """Split at separators that are not inside {{ }}, [[ ]] or [ ]."""
    parts, depth, start, i = [], 0, 0, 0
    while i < len(text):
        two = text[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            i += 2
            continue
        if two in ("}}", "]]") and depth:
            depth -= 1
            i += 2
            continue
        if text[i] == separator and depth == 0:
            parts.append(text[start:i])
            start = i + 1
        i += 1
    parts.append(text[start:])
    return parts


def templates(text):
    """Yield (start, end, name, args) for each top-level {{template}} in text.

    args is a list of (key or None, value) pairs; positional arguments have
    key None.
    """
    i = 0
    while True:
        start = text.find("{{", i)
        if start == -1:
            return
        depth, j = 0, start
        while j < len(text):
            if text.startswith("{{", j):
                depth += 1
                j += 2
            elif text.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        if depth:
            return
        inner = text[start + 2:j - 2]
        pieces = split_top_level(inner)
        name = pieces[0].strip()
        args = []
        for piece in pieces[1:]:
            key, eq, value = piece.partition("=")
            if eq and re.fullmatch(r"\s*[\w -]+\s*", key) and "[[" not in key:
                args.append((key.strip().lower(), value))
            else:
                args.append((None, piece))
        yield start, j, name, args
        i = j


def arg(args, *keys, position=None):
    """A named argument, or the nth positional one (1-based)."""
    for key, value in args:
        if key in keys or (key is not None and key.isdigit() and position and int(key) == position):
            return value
    if position:
        positional = [value for key, value in args if key is None]
        if len(positional) >= position:
            return positional[position - 1]
    return None


def description_field(wikitext, field):
    """The value of a field of the file description template, or None."""
    for _, _, name, args in templates(wikitext or ""):
        if name.strip().lower() in DESCRIPTION_TEMPLATES:
            for key, value in args:
                if key == field:
                    return value
    return None


# ------------------------------------------------------------- rendering

class AuthorReader:
    """Turns author wikitext into plain text, with caching of API lookups."""

    def __init__(self):
        self.rendered = {}
        self.labels = {}

    def wikidata_label(self, qid):
        qid = qid.strip().upper()
        if qid not in self.labels:
            query = urllib.parse.urlencode({"action": "wbgetentities", "format": "json", "ids": qid,
                                            "props": "labels", "languages": "en|mul"})
            entity = json.loads(http_get(f"{WIKIDATA_API}?{query}"))["entities"].get(qid, {})
            labels = entity.get("labels", {})
            label = (labels.get("en") or labels.get("mul") or {}).get("value")
            self.labels[qid] = label or qid
        return self.labels[qid]

    def parse_remotely(self, wikitext):
        """Render wikitext with the Commons parser and return its text."""
        if wikitext not in self.rendered:
            query = urllib.parse.urlencode({"action": "parse", "format": "json", "formatversion": "2",
                                            "contentmodel": "wikitext", "prop": "text", "disablelimitreport": "1",
                                            "text": wikitext})
            page = json.loads(http_get(f"{COMMONS_API}?{query}"))["parse"]["text"]
            # Hidden helper text (machine-readable copies, tooltips) is not
            # part of what a reader sees.
            page = re.sub(r'<(\w+)[^>]*(?:display:\s*none|class="[^"]*hidden[^"]*")[^>]*>.*?</\1>', "", page,
                          flags=re.S)
            self.rendered[wikitext] = html.unescape(re.sub(r"<[^>]+>", " ", page))
        return self.rendered[wikitext]

    def template(self, name, args):
        key = name.strip().lower().replace("_", " ")
        if key in USER_LINK_TEMPLATES:
            return self.text(arg(args, "1", position=1) or "")
        if key in ("w", "wp", "wd"):
            target = self.text(arg(args, "1", position=1) or "")
            label = arg(args, "2", position=2)
            if re.fullmatch(r"[Qq]\d+", target.strip()):
                return self.wikidata_label(target)
            return self.text(label) if label else target
        if key == "autvec":
            original = self.text(arg(args, "o", "1", position=1) or "").lstrip(".").strip()
            vector = self.text(arg(args, "v", "2", position=2) or "").lstrip(".").strip()
            if original.lower() in ("", "u", "-", "?"):
                original = "unknown"
            parts = [f"{original} (design)"]
            if vector:
                parts.append(f"{vector} (vector drawing)")
            return "; ".join(parts)
        if key == "unknown":
            return "unknown author"
        if key == "creator":
            qid = arg(args, "wikidata")
            return self.wikidata_label(qid) if qid else self.text(arg(args, "1", position=1) or "")
        if key.startswith("creator:"):
            return name.split(":", 1)[1].strip()
        if key in ("original uploader", "author assumed", "own assumed"):
            return self.text(arg(args, "1", position=1) or "")
        if key in NOT_AN_AUTHOR:
            return ""
        if key.startswith("user:"):
            # A user's own signature template ({{User:Heraldry/I}}) names
            # that user.
            return name.split(":", 1)[1].split("/", 1)[0].strip()
        if key in NOTICE_TEMPLATES or key.startswith(("defaultsort", "int:")):
            return ""
        from commons_license import tag_kind
        if tag_kind(key) is not None or key.startswith(("self", "pd-", "cc-", "gfdl")):
            return ""
        return self.parse_remotely("{{" + name + "".join(
            "|" + (f"{k}={v}" if k else v) for k, v in args) + "}}")

    def text(self, wikitext):
        """Plain text of a piece of wikitext."""
        text = wikitext or ""
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        text = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S | re.I)
        # A closing </ref> without its opening tag ends a citation the editor
        # forgot to open, which starts after the previous line break.
        text = re.sub(r"<br\s*/?>[^<]*?</ref>", "", text, flags=re.I)
        text = re.sub(r"</ref>", "", text, flags=re.I)
        # Signature decorations ("(talk)" links in small or subscript type).
        text = re.sub(r"<(sub|sup|small)>.*?</\1>", "", text, flags=re.S | re.I)
        # List bullets inside the field separate several credits.
        text = re.sub(r"\n\s*\*\s*", "; ", text)
        out, last = [], 0
        for start, end, name, args in templates(text):
            out.append(text[last:start])
            out.append(self.template(name, args))
            last = end
        out.append(text[last:])
        text = "".join(out)

        def link(match):
            target, _, label = match.group(1).partition("|")
            target = target.strip().lstrip(":")
            if re.match(r"(?i)(user[ _]talk|special|category):", target):
                return ""
            if label.strip():
                return label
            return re.sub(r"^(?:[a-z-]+:)*(?:user:)?", "", target, flags=re.I)

        text = re.sub(r"\[\[([^\[\]]*)\]\]", link, text)
        text = re.sub(r"\[(?:https?:)?//[^\s\]]+\s+([^\]]*)\]", r"\1", text)
        text = re.sub(r"(?:https?:)?//[^\s\]]+", "", text)
        text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("'''", "").replace("''", "")
        text = html.unescape(text)
        # Brackets left with nothing but punctuation once links are gone
        # ("(talk)" after dropping the talk link, "[ ]" around a bare URL).
        for _ in range(3):
            text = re.sub(r"[\(\[]\s*[•·|,;:/\-–]*\s*[\)\]]", "", text)
        # A single bracket pair that is not a link any more.
        text = re.sub(r"\[\s*([^\[\]]*?)\s*\]", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,;:.)])", r"\1", text)
        return text.strip(" ,;:")


def all_templates(text):
    """Every template in text, including ones nested in other templates."""
    for start, end, name, args in templates(text or ""):
        yield name, args
        for _, value in args:
            yield from all_templates(value)


def release_author(wikitext):
    """The author named by a public-domain release or {{self}} license."""
    for name, args in all_templates(wikitext):
        key = name.strip().lower()
        if key == "pd-openclipart":
            return "Open Clip Art Library"
        if key.startswith(("pd-user", "pd-author")):
            value = arg(args, "1", position=1)
            if value and value.strip():
                return value
        if key.startswith(("pd-self", "self", "gfdl-self", "gfdl-user")):
            value = arg(args, "author")
            if value and value.strip():
                return value
            if key.startswith("gfdl-user"):
                value = arg(args, "1", position=1)
                if value and value.strip():
                    return value
    return None


def first_uploader(title):
    """The user who uploaded the first revision of a Commons file."""
    query = urllib.parse.urlencode({"action": "query", "format": "json", "formatversion": "2",
                                    "prop": "imageinfo", "iiprop": "user", "iilimit": "max",
                                    "titles": "File:" + title})
    page = json.loads(http_get(f"{COMMONS_API}?{query}"))["query"]["pages"][0]
    history = page.get("imageinfo") or []
    return history[-1]["user"] if history else None


def author_of(title, wikitext, reader):
    """The author of a file as its page names them, or None."""
    field = description_field(wikitext, "author")
    text = reader.text(field) if field else ""
    if not text or text.lower() in NOT_AN_AUTHOR:
        fallback = release_author(wikitext)
        text = reader.text(fallback) if fallback else ""
    if not text or text.lower() in NOT_AN_AUTHOR:
        uploader = first_uploader(title)
        text = f"{uploader} (uploader)" if uploader else ""
    return text or None
