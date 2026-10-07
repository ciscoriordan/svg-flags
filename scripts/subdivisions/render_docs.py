#!/usr/bin/env python3
"""Write the README tables and gallery sections for the pipeline's countries.

For each country in flags.json this rewrites its table under "Subdivisions
(ISO 3166-2)" in README.md and its block under "Subdivisions" in the four
gallery pages, inserting the section in order if it does not exist yet.
Rows for flags that were added by hand (ca-bc, ca-qc, ch-gr) are kept as
they are, and rows for codes listed under "excluded" are removed; rows are
sorted by code. Running the script twice changes nothing.

Flags whose artwork asks for credit (CC BY, CC BY-SA, or an author's own
attribution terms, as lock_sources.py records them) get a credit entry in a
generated block at the end of the README's Credits section. It names the
subdivision and code, the Commons file with its author, the other users who
uploaded the versions the pinned revision descends from, its license, any
file the drawing was built from whose license also holds, and how the four
files differ from the drawing: what the full-size files change on purpose
("clean" and "canvas" options), and whether the circle and square files are
crops, zoomed-out views with the field continued, or recompositions (a
recipe's "adaptation" text replaces that last part where it says more). For
share-alike artwork it also says that the flag's four files are distributed
under that license instead of MIT.

The same entries, with the paths of the four files, make up NOTICE.md, which
LICENSE points to for the files that are not MIT; NOTICE.md is removed when
no flag needs credit.

Colors: flags with at most six flat colors list them as swatches linked to
the Commons file, like the hand-made rows; detailed coats of arms leave the
cell empty, like the US seal flags. Missing swatch files are created.

Usage: render_docs.py [COUNTRY ...]   (default: every country in flags.json)
"""

import os
import re
import sys
import urllib.parse

from lxml import etree

import svgtools as st
from build_variants import layout_for, window_for
from common import REPO, VARIANTS, load_flags, load_sources

TABLE_HEADER = ("| Code | Name | Circle | Square | Simplified | Full-size | Colors |\n"
                "|------|------|:------:|:----:|:----------:|:---------:|--------|\n")
GALLERIES = {
    "index.html": '<img class="circle" src="circle/states/{code}.svg" width="96" height="96"/>',
    "gallery-square.html": '<img class="square" src="square/states/{code}.svg" width="96" height="96"/>',
    "gallery-full-size-simplified.html": '<img src="full-size-simplified/states/{code}.svg" height="72"/>',
    "gallery-full-size.html": '<img src="full-size/states/{code}.svg" height="72"/>',
}
MAX_SWATCHES = 6
CREDITS_START = "<!-- subdivision flag credits, written by scripts/subdivisions/render_docs.py -->"
CREDITS_END = "<!-- end of subdivision flag credits -->"
NOTICE = REPO / "NOTICE.md"
# What a full-size file changes on purpose, by recipe option.
FULL_SIZE_CHANGES = {
    "drop_blurred": "leave out its blurred shadows",
    "flatten_images": "draw its embedded raster shading as flat color",
}
# How the circle and square files show the drawing, as nouns: (one, several).
VARIANT_KINDS = {
    "crop": ("a crop of it", "crops of it"),
    "zoom": ("a zoomed-out view of it with its field continued past its edges",
             "zoomed-out views of it with its field continued past its edges"),
    "layers": ("a recomposition of parts of it", "recompositions of parts of it"),
}


def ordered_colors(svg_text):
    """Colors in order of first appearance, as validate-swatches.py reads them."""
    seen = []
    for value in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,6})"', svg_text):
        color = st.normalize_color(value)
        if color != "#CDCFD3" and color not in seen:
            seen.append(color)
    return seen


def colors_cell(code, source):
    full = (REPO / "full-size" / "states" / f"{code}.svg").read_text(encoding="utf-8")
    circle = (REPO / "circle" / "states" / f"{code}.svg").read_text(encoding="utf-8")
    colors = ordered_colors(circle)
    if "Gradient" in full or len(colors) > MAX_SWATCHES:
        return "", []
    page = source["commons_page"]
    cells = [f'[<img src="swatches/{c[1:]}.svg" width="12">&nbsp;`{c}`]({page})' for c in colors]
    return "<br>".join(cells), colors


def readme_row(code, recipe, source):
    article = urllib.parse.quote(source["wikipedia"], safe="_(),")
    colors, _ = colors_cell(code, source)
    return (f"| `{code}` | [{recipe['name']}](https://en.wikipedia.org/wiki/{article}) "
            f'| <img src="circle/states/{code}.svg" width="32"> '
            f'| <img src="square/states/{code}.svg" width="32"> '
            f"| [✓](full-size-simplified/states/{code}.svg) | [✓](full-size/states/{code}.svg) | {colors} |")


def split_blocks(text, heading):
    """Split text into (preamble, [(title, block)]) at lines starting with heading."""
    parts = re.split(rf"(?m)^(?={re.escape(heading)} )", text)
    blocks = []
    for part in parts[1:]:
        title = part.split("\n", 1)[0][len(heading) + 1:].strip()
        blocks.append((title, part))
    return parts[0], blocks


def linked_license(name, url):
    return f"[{name}]({url})" if url else name


def names(items):
    """'A', 'A and B', 'A, B and C'."""
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def variant_kind(layout, width, height):
    """How one variant shows the drawing: "crop", "zoom" or "layers"."""
    if "layers" in layout:
        return "layers"
    x, y, side = window_for(layout, width, height)
    unit = min(width, height)
    inside = x >= -1e-6 and y >= -1e-6 and x + side <= width / unit + 1e-6 and y + side <= height / unit + 1e-6
    return "crop" if inside else "zoom"


def changes_sentence(code, recipe):
    """How the four files differ from the Commons drawing."""
    sentences = []
    full = [text for option, text in FULL_SIZE_CHANGES.items() if recipe.get("clean", {}).get(option)]
    if recipe.get("canvas"):
        full.append("extend its field to the proportions the flag's law gives")
    if full:
        sentences.append(f"The full-size files {names(full)}.")
    if recipe.get("adaptation"):
        sentences.append(f"The circle and square files {recipe['adaptation']}.")
    else:
        root = etree.parse(str(REPO / "full-size" / "states" / f"{code}.svg")).getroot()
        vb = st.viewbox(root)
        circle, square = (variant_kind(layout_for(recipe, v), vb[2], vb[3]) for v in ("circle", "square"))
        if circle == square:
            sentences.append(f"The circle and square files are {VARIANT_KINDS[circle][1]}.")
        else:
            sentences.append(f"The circle file is {VARIANT_KINDS[circle][0]}, and the square file is "
                             f"{VARIANT_KINDS[square][0]}.")
    return " ".join(sentences)


def credit_text(code, recipe, source):
    """Who to credit for a flag whose artwork asks for credit, and under what terms."""
    author = source["author"]
    own, own_url = source["own_license"], source["own_license_url"]
    if source.get("own_kind") == "release":
        terms = "released into the public domain"
    elif source.get("own_kind") == "design":
        # A tag such as {{PD-Coa-Mexico}} is a claim about the coat of arms;
        # it is not a release or license from the person who drew the file.
        terms = "tagged only as a public-domain design"
    elif own == "attribution as the author requests":
        terms = f"credited as the author asks ({linked_license('terms', own_url)})"
    else:
        terms = linked_license(own, own_url)
    parts = [f"[{source['commons_title']}]({source['commons_page']}) by {author}"]
    if source.get("contributors"):
        parts.append(f", with versions uploaded by {names(source['contributors'])}")
    parts.append(f", {terms}")
    for part in source.get("derived_from", []):
        if part["binding"]:
            parts.append(f", based on [{part['title']}]({part['page']}) by {part['author']}, "
                         f"{linked_license(part['license'], part['license_url'])}")
    parts.append(". " + changes_sentence(code, recipe))
    if source["license_kind"] == "share-alike":
        parts.append(f" All four `{code}` files are distributed under "
                     f"{linked_license(source['license'], source['license_url'])} instead of MIT.")
    return "".join(parts)


def credit_line(code, recipe, source):
    """The README credit entry for a flag whose artwork asks for credit."""
    return f"- `{code}` {recipe['name']}: {credit_text(code, recipe, source)}"


def notice_text(flags, sources):
    """NOTICE.md: the files that are not MIT, with their licenses and credits,
    or None when every file is MIT."""
    credited = [code for code in sorted(flags) if sources[code].get("attribution_required")]
    if not credited:
        return None
    lines = [
        "# Notices",
        "",
        "Most of this repository is under the MIT license in [LICENSE](LICENSE). The files listed here are not. "
        "They are built from artwork on Wikimedia Commons whose license asks for credit, and they keep that "
        "license. Anyone who copies or shows them, including an app that streams them through the SVGFlags "
        "package, has to credit them as given here, and files under CC BY-SA have to stay under CC BY-SA, "
        "adaptations included.",
        "",
        "[`scripts/subdivisions/render_docs.py`](scripts/subdivisions/render_docs.py) writes this file from "
        "[`scripts/subdivisions/sources.json`](scripts/subdivisions/sources.json), which also records every "
        "license tag each license was worked out from.",
        "",
    ]
    for code in credited:
        source = sources[code]
        files = ", ".join(f"`{variant}/states/{code}.svg`" for variant in VARIANTS)
        lines += [
            f"## `{code}` {flags[code]['name']}",
            "",
            f"- Files: {files}",
            f"- License: {linked_license(source['license'], source['license_url'])}",
            f"- Credit: {credit_text(code, flags[code], source)}",
            "",
        ]
    return "\n".join(lines)


def update_notice(flags, sources):
    text = notice_text(flags, sources)
    if text is None:
        NOTICE.unlink(missing_ok=True)
    else:
        NOTICE.write_text(text, encoding="utf-8")


def update_credits(flags, sources):
    path = REPO / "README.md"
    text = path.read_text(encoding="utf-8")
    if CREDITS_START in text:
        start = text.index(CREDITS_START)
        end = text.index(CREDITS_END) + len(CREDITS_END)
        text = (text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")).rstrip("\n") + "\n"
    lines = [credit_line(code, flags[code], sources[code]) for code in sorted(flags)
             if sources[code].get("attribution_required")]
    if lines:
        block = (f"{CREDITS_START}\n\n### Subdivision flag artwork\n\n"
                 "These subdivision flags are drawn from Wikimedia Commons artwork whose license asks for credit. "
                 "For each code, `full-size/states/<code>.svg` and `full-size-simplified/states/<code>.svg` are the "
                 "drawing converted for Xcode (styles turned into attributes, references expanded, ids renamed, "
                 "coordinates rounded), with any further change named in its entry, and "
                 "`circle/states/<code>.svg` and `square/states/<code>.svg` are made from it as the entry says. "
                 "These files keep the license of their source, as listed here and in [NOTICE.md](NOTICE.md), "
                 "instead of MIT. [`scripts/subdivisions/sources.json`](scripts/subdivisions/sources.json) records "
                 "every license tag each license was worked out from.\n\n" + "\n".join(lines)
                 + f"\n\n{CREDITS_END}\n")
        start = text.index("\n## Credits\n")
        end = text.find("\n## ", start + 1)
        end = len(text) if end == -1 else end + 1
        text = text[:end].rstrip("\n") + "\n\n" + block + ("\n" + text[end:] if end < len(text) else "")
    path.write_text(text, encoding="utf-8")


def update_readme(countries, flags, sources, excluded):
    path = REPO / "README.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("### Subdivisions (ISO 3166-2)\n")
    end = text.index("\n### ", start + 1) + 1
    preamble, blocks = split_blocks(text[start:end], "####")
    for cc, country in countries.items():
        ours = sorted(c for c in flags if c.startswith(cc + "-"))
        index = next((i for i, (title, _) in enumerate(blocks) if title == country["name"]), None)
        rows = {}
        if index is not None:
            for line in blocks[index][1].splitlines():
                m = re.match(r"\| `([a-z0-9-]+)` \|", line)
                if m and m.group(1) not in ours and m.group(1) not in excluded:
                    rows[m.group(1)] = line
        for code in ours:
            rows[code] = readme_row(code, flags[code], sources[code])
        note = f"{country['note']}\n\n" if country.get("note") else ""
        block = (f"#### {country['name']}\n\n{note}{TABLE_HEADER}"
                 + "".join(rows[c] + "\n" for c in sorted(rows)) + "\n")
        if index is not None:
            blocks[index] = (country["name"], block)
        else:
            # Sections are in alphabetical order of the country name.
            at = next((i for i, (title, _) in enumerate(blocks) if title > country["name"]), len(blocks))
            blocks.insert(at, (country["name"], block))
    section = preamble + "".join(block for _, block in blocks)
    path.write_text(text[:start] + section + text[end:], encoding="utf-8")


GALLERY_ITEM = re.compile(r'  <div class="flag-item">\n.*?<div class="flag-code">([^<]+)</div>\n  </div>\n', re.S)


def update_gallery(name, image, countries, flags, excluded):
    path = REPO / name
    text = path.read_text(encoding="utf-8")
    start = text.index("<h2>Subdivisions</h2>")
    end = text.index("<h2>", start + 1)
    parts = re.split(r"(?m)^(?=<h3>)", text[start:end])
    preamble, blocks = parts[0], []
    for part in parts[1:]:
        title = re.match(r"<h3>(.*?)</h3>", part).group(1)
        codes = re.findall(r'<div class="flag-code">([^<]+)</div>', part)
        blocks.append([title, part, codes[0].split("-")[0] if codes else ""])
    for cc, country in countries.items():
        ours = sorted(c for c in flags if c.startswith(cc + "-"))
        index = next((i for i, b in enumerate(blocks) if b[0] == country["name"]), None)
        items = {}
        if index is not None:
            for m in GALLERY_ITEM.finditer(blocks[index][1]):
                if m.group(1) not in ours and m.group(1) not in excluded:
                    items[m.group(1)] = m.group(0)
        for code in ours:
            items[code] = ('  <div class="flag-item">\n'
                           f"    {image.format(code=code)}\n"
                           f'    <div class="flag-name">{flags[code]["name"]}</div>\n'
                           f'    <div class="flag-code">{code}</div>\n'
                           "  </div>\n")
        block = (f"<h3>{country['name']}</h3>\n<div class=\"flags\">\n"
                 + "".join(items[c] for c in sorted(items)) + "</div>\n\n")
        if index is not None:
            blocks[index][1] = block
        else:
            # Gallery sections are in order of the country code.
            at = next((i for i, b in enumerate(blocks) if b[2] > cc), len(blocks))
            blocks.insert(at, [country["name"], block, cc])
    section = preamble + "".join(b[1] for b in blocks)
    path.write_text(text[:start] + section + text[end:], encoding="utf-8")


def write_swatches(flags, sources):
    folder = REPO / "swatches"
    # Compare names exactly: on a case-insensitive disk, d80027.svg would hide
    # a missing D80027.svg that GitHub Pages needs.
    existing = set(os.listdir(folder))
    created = []
    for code in sorted(flags):
        _, colors = colors_cell(code, sources[code])
        for color in colors:
            name = f"{color[1:]}.svg"
            if name in existing:
                continue
            if name.lower() in {e.lower() for e in existing}:
                raise SystemExit(f"swatches/{name} differs only in case from an existing file; rename it first")
            (folder / name).write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12">'
                f'<rect width="12" height="12" fill="{color}"/></svg>\n', encoding="utf-8")
            existing.add(name)
            created.append(name)
    return created


def main():
    data = load_flags()
    countries = data["countries"]
    excluded = set(data.get("excluded", {}))
    if sys.argv[1:]:
        unknown = set(sys.argv[1:]) - set(countries)
        if unknown:
            sys.exit(f"not in flags.json: {' '.join(sorted(unknown))}")
        countries = {cc: countries[cc] for cc in sys.argv[1:]}
    flags = {code: recipe for code, recipe in data["flags"].items() if code.split("-")[0] in countries}
    sources = load_sources()
    update_readme(countries, flags, sources, excluded)
    for name, image in GALLERIES.items():
        update_gallery(name, image, countries, flags, excluded)
    # Credits cover every flag, whichever countries were asked for.
    update_credits(data["flags"], sources)
    update_notice(data["flags"], sources)
    created = write_swatches(flags, sources)
    print(f"README.md and {len(GALLERIES)} gallery pages updated; {len(created)} new swatches")


if __name__ == "__main__":
    main()
