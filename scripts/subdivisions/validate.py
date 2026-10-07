#!/usr/bin/env python3
"""Check the subdivision flags built by this pipeline.

For every flag in flags.json, all four variants must exist and:
  - contain nothing CoreSVG cannot draw (<mask>, <style>, class, <use>,
    xlink:href or href, <image>, <text>, <filter>, <marker>), and no symlinks;
  - have a viewBox; circle and square are 512x512 with viewBox 0 0 512 512 and
    an outer group clipped by <circle cx=256 cy=256 r=256> or <rect 512x512>;
  - resolve every url(#id) to exactly one element, with no duplicate ids;
  - write a border, if any, exactly as the README shows it (the border
    strippers match that text);
  - use uppercase 6-digit hex colors, and in circle/square only colors that
    the full-size flag uses (plus the border grey);
  - have a pinned source in sources.json with a known license and an author,
    and, when that license asks for credit (CC BY, CC BY-SA or an author's
    own attribution terms), the credit entry render_docs.py writes into the
    README;
  - stay within the size budget: circle and square warn above 100 KB and fail
    above 238 KB (the largest flag that predates this pipeline), unless listed
    in SIZE_EXCEPTIONS; full-size warns above 1 MB.

Codes left out on purpose (flags.json "excluded") must have no files in the
variant folders. NOTICE.md must be exactly what render_docs.py writes (the
files that keep their artwork's license instead of MIT), and LICENSE must
point to it whenever it lists any file.

With --render it also renders every flag:
  - circle and square at the sizes where each line along which the artwork
    meets the fills of its layout lands across a pixel, directly and as an
    8x supersampled render scaled down: a pixel row or column along such a
    line that differs between the two is a seam, where the antialiased
    edges of stacked shapes let the color underneath show through (the
    "covers" recipe option hides them);
  - full-size against the pinned Commons original (rsvg) at 1200 pixels: at
    most 0.02% of pixels may move by more than 40 levels, and no connected
    group of changed pixels may be larger than 24 pixels, so a missing or
    reshaped element fails even when it is small (needs fetch.py to have
    run). For a recipe with "canvas", the area of the original is compared;
  - on macOS, CoreSVG against rsvg for all variants: at most 1% of pixels may
    differ, which catches anything CoreSVG skips or draws differently.

With --repo the structural rules also run over every other SVG in the four
variant folders. Problems there predate this pipeline and are reported as
warnings only.

Usage: validate.py [--render] [--repo] [CODE or COUNTRY ...]
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

from lxml import etree
from PIL import Image

import svgtools as st
from common import (REPO, VARIANTS, commons_cache_path, compare_renders, coresvg_available, coresvg_render,
                    drift_limits, fidelity, load_flags, load_sources, render, select_codes)
from build_variants import art_edges, layout_for
from commons_author import looks_like_license
from render_docs import NOTICE, credit_line, notice_text

FORBIDDEN = re.compile(r"<(mask|style|use|image|text|filter|marker|foreignObject|script)\b|\sclass=|\s(xlink:)?href=")
BORDER_TEXT = {
    "circle": '<!-- border --><circle cx="256" cy="256" r="256" fill="none" stroke="#cdcfd3" stroke-width="16"/>',
    "square": '<!-- border --><rect width="512" height="512" fill="none" stroke="#cdcfd3" stroke-width="16"/>',
}
CLIP_SHAPE = {"circle": ("circle", {"cx": "256", "cy": "256", "r": "256"}),
              "square": ("rect", {"width": "512", "height": "512"})}
TARGET_BYTES = 100_000
MAX_BYTES = 238_293  # square/states/us-vt.svg, the largest flag before this pipeline
FULL_SIZE_WARN_BYTES = 1_000_000
# Coats of arms whose detail cannot be rounded further without visible damage,
# with the reason.
SIZE_EXCEPTIONS = {
    "ar-l": "the provincial arms are built from about 900 small shapes; rounding them one decimal coarser (whole "
            "units of the full-size drawing) changes 0.5% of the pixels at 1024 px",
    "mx-oax": "the arms fill the circle with fine lettering and line work; rounding them one decimal coarser "
              "changes 5% of the pixels at 1024 px",
}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, path, message):
        self.errors.append(f"{path}: {message}")

    def warn(self, path, message):
        self.warnings.append(f"{path}: {message}")


def structural(path, report, strict):
    """Rules that apply to any flag file; strict adds the pipeline-only rules."""
    flag = report.error if strict else report.warn
    rel = path.relative_to(REPO)
    if path.is_symlink():
        flag(rel, "is a symlink")
        return
    text = path.read_text(encoding="utf-8")
    try:
        root = etree.fromstring(text.encode())
    except etree.XMLSyntaxError as error:
        flag(rel, f"is not well-formed XML: {error}")
        return
    # Comments may describe unsupported elements that were already expanded.
    markup = etree.tostring(etree.fromstring(text.encode(), etree.XMLParser(remove_comments=True)),
                            encoding="unicode")
    m = FORBIDDEN.search(markup)
    if m:
        flag(rel, f"contains {m.group(0).strip()!r}, which CoreSVG does not support")
    ids = [e.get("id") for e in root.iter() if isinstance(e.tag, str) and e.get("id")]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        flag(rel, f"id {dup!r} is defined more than once")
    for ref in sorted(set(st.URL_REF.findall(text))):
        if ref not in ids:
            flag(rel, f"url(#{ref}) does not resolve")
    variant = rel.parts[0]
    if variant in BORDER_TEXT and "<!-- border -->" in text:
        for found in re.findall(r"<!--\s*border\s*-->\s*<[^>]*>", text):
            if found != BORDER_TEXT[variant]:
                flag(rel, f"border is not written as {BORDER_TEXT[variant]!r}")
    if not strict:
        return root
    if root.get("viewBox") is None:
        report.error(rel, "has no viewBox")
    for value in re.findall(r'(?:fill|stroke|stop-color)="(#[^"]*)"', text):
        if value != "#cdcfd3" and not re.fullmatch(r"#[0-9A-F]{6}", value):
            report.error(rel, f"color {value} is not uppercase 6-digit hex")
            break
    if variant in CLIP_SHAPE:
        if (root.get("width"), root.get("height"), root.get("viewBox")) != ("512", "512", "0 0 512 512"):
            report.error(rel, "is not 512x512 with viewBox 0 0 512 512")
        groups = [c for c in root if st.local(c) == "g"]
        clip_ref = st.URL_REF.search(groups[0].get("clip-path", "")) if len(groups) == 1 else None
        clip = next((e for e in root.iter() if clip_ref and e.get("id") == clip_ref.group(1)), None)
        shape, attrs = CLIP_SHAPE[variant]
        if clip is None or len(clip) != 1 or st.local(clip[0]) != shape or \
                {k: v for k, v in clip[0].attrib.items()} != attrs:
            report.error(rel, f"content is not inside one group clipped by a 512 {shape}")
    return root


def check_flag(code, sources, flags, readme, report):
    paths = {v: REPO / v / "states" / f"{code}.svg" for v in VARIANTS}
    for variant, path in paths.items():
        if not path.exists():
            report.error(path.relative_to(REPO), "is missing")
    if not all(p.exists() for p in paths.values()):
        return
    for path in paths.values():
        structural(path, report, strict=True)
    full_colors = st.colors_in(paths["full-size"].read_text(encoding="utf-8"))
    for variant in ("circle", "square"):
        extra = st.colors_in(paths[variant].read_text(encoding="utf-8")) - full_colors - {"#CDCFD3"}
        if extra:
            report.error(paths[variant].relative_to(REPO), f"uses colors not in the full-size flag: {sorted(extra)}")
        size = paths[variant].stat().st_size
        rel = paths[variant].relative_to(REPO)
        if size > MAX_BYTES and code not in SIZE_EXCEPTIONS:
            report.error(rel, f"is {size // 1000} KB, above the {MAX_BYTES // 1000} KB budget")
        elif size > TARGET_BYTES:
            report.warn(rel, f"is {size // 1000} KB, above the {TARGET_BYTES // 1000} KB target")
    if paths["full-size"].stat().st_size > FULL_SIZE_WARN_BYTES:
        report.warn(paths["full-size"].relative_to(REPO), "is larger than 1 MB")
    if paths["full-size"].read_bytes() != paths["full-size-simplified"].read_bytes():
        report.error(paths["full-size-simplified"].relative_to(REPO), "differs from full-size")

    source = sources.get(code)
    if source is None:
        report.error("sources.json", f"has no record for {code}")
        return
    kind = source.get("license_kind")
    if kind not in ("public domain", "attribution", "share-alike"):
        report.error("sources.json", f"{code} has no usable license ({source.get('license')!r}); run lock_sources.py")
    elif not source.get("author") or looks_like_license(source["author"]):
        report.error("sources.json", f"{code} has no author, or one that reads like license text; "
                                     f"run lock_sources.py")
    elif source.get("attribution_required") != (kind != "public domain"):
        report.error("sources.json", f"{code} is {kind} but attribution_required says otherwise; "
                                     f"run lock_sources.py")
    elif kind != "public domain" and credit_line(code, flags[code], source) not in readme:
        report.error("README.md", f"does not credit {code} ({source['license']}); run render_docs.py")
    if flags[code]["commons"] != source["commons_title"]:
        report.error("sources.json", f"{code} is pinned to {source['commons_title']!r}, not the recipe's file")


def check_exclusions(data, report):
    """Codes left out on purpose must not ship."""
    excluded, flags = data.get("excluded", {}), data["flags"]
    for code in sorted(set(excluded) & set(flags)):
        report.error("flags.json", f"{code} is both built and listed under \"excluded\"")
    for code in sorted(excluded):
        for variant in VARIANTS:
            path = REPO / variant / "states" / f"{code}.svg"
            if path.exists():
                report.error(path.relative_to(REPO), "exists, but the flag is listed under \"excluded\"")


def check_notice(flags, sources, report):
    """NOTICE.md lists the files that are not MIT, and LICENSE says so."""
    expected = notice_text(flags, sources)
    if expected is None:
        if NOTICE.exists():
            report.error("NOTICE.md", "exists, but no flag needs credit; run render_docs.py")
        return
    if not NOTICE.exists() or NOTICE.read_text(encoding="utf-8") != expected:
        report.error("NOTICE.md", "is not what render_docs.py writes from sources.json; run render_docs.py")
    if "NOTICE.md" not in (REPO / "LICENSE").read_text(encoding="utf-8"):
        report.error("LICENSE", "does not exclude the files listed in NOTICE.md from the MIT license")


def difference(a, b):
    """Share of pixels that changed between two renders of the same size."""
    return compare_renders(a, b)[0]


# Typical on-screen sizes in pixels: 22 to 44 points on 2x and 3x screens.
SEAM_SIZES = (44, 48, 64, 66, 72, 88, 96, 132)
SEAM_LEVELS = 24
# A seam is a visible line: this many neighboring pixels along the edge
# that moved. A lone pixel is ordinary antialiasing.
SEAM_RUN = 3


def seam_sizes(position):
    """The listed render sizes at which a line at this position (in 512
    units) falls well inside a pixel rather than on a pixel boundary, which
    is where seams show."""
    return [n for n in SEAM_SIZES if 0.1 <= (position * n / 512) % 1 <= 0.9]


def check_seams(code, recipe, report):
    full = REPO / "full-size" / "states" / f"{code}.svg"
    root = etree.parse(str(full)).getroot()
    vb = st.viewbox(root)
    renders = {}
    for variant in ("circle", "square"):
        path = REPO / variant / "states" / f"{code}.svg"
        for axis, position, start, end in art_edges(layout_for(recipe, variant), vb[2], vb[3]):
            for n in seam_sizes(position):
                if (variant, n) not in renders:
                    direct = render(path, n, n).convert("RGBA")
                    fine = render(path, n * 8, n * 8).convert("RGBA").resize((n, n), Image.BOX)
                    renders[variant, n] = (direct.load(), fine.load())
                direct, fine = renders[variant, n]
                line = int(position * n / 512)
                run = longest = 0
                for k in range(int(start * n / 512) + 1, int(end * n / 512) - 1):
                    x, y = (line, k) if axis == "x" else (k, line)
                    # The rim of the circle and the border stroke are
                    # antialiased differently by design; only the inside
                    # counts.
                    inside = (((x + 0.5 - n / 2) ** 2 + (y + 0.5 - n / 2) ** 2) ** 0.5 <= n / 2 - 2
                              if variant == "circle" else min(x, y, n - 1 - x, n - 1 - y) >= 2)
                    a, b = direct[x, y], fine[x, y]
                    if inside and max(abs(a[i] - b[i]) for i in range(3)) > SEAM_LEVELS:
                        run += 1
                        longest = max(longest, run)
                    else:
                        run = 0
                if longest >= SEAM_RUN:
                    where = "column" if axis == "x" else "row"
                    report.error(path.relative_to(REPO), f"shows a seam along {where} {line} at {n} px, where the "
                                                         f"artwork meets the fills ({axis} = {position:.1f}); "
                                                         f"add covers")
                    break


def check_renders(codes, flags, report):
    jobs, pairs = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for code in codes:
            check_seams(code, flags[code], report)
            full = REPO / "full-size" / "states" / f"{code}.svg"
            root = etree.parse(str(full)).getroot()
            height = round(400 * float(root.get("height")) / float(root.get("width")))
            original = commons_cache_path(code)
            if original.exists():
                share, region = fidelity(original, full, flags[code])
                max_share, max_region = drift_limits(flags[code])
                if share > max_share or region > max_region:
                    report.error(full.relative_to(REPO), f"differs from the Commons original on {share:.3%} of "
                                                         f"pixels, in a patch of up to {region} pixels")
            else:
                report.warn(full.relative_to(REPO), "Commons original not downloaded (run fetch.py); fidelity not checked")
            for variant, size in (("circle", (256, 256)), ("square", (256, 256)), ("full-size", (400, height))):
                path = REPO / variant / "states" / f"{code}.svg"
                png = Path(tmp) / f"{variant}-{code}.png"
                jobs.append((path, png, *size))
                pairs.append((path, png, size))
        if not coresvg_available():
            report.warn("CoreSVG", "not available on this system; cross-renderer check skipped")
            return
        failed = coresvg_render(jobs)
        for path, png, size in pairs:
            rel = path.relative_to(REPO)
            if str(path) in failed or not png.exists():
                report.error(rel, "CoreSVG could not load it")
                continue
            moved = difference(render(path, *size), Image.open(png).convert("RGBA"))
            if moved > 0.01:
                report.error(rel, f"CoreSVG and rsvg disagree on {moved:.2%} of pixels")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--render", action="store_true", help="also compare renders (slower)")
    parser.add_argument("--repo", action="store_true", help="also check every other flag in the repo")
    parser.add_argument("codes", nargs="*")
    args = parser.parse_args()

    data = load_flags()
    flags = data["flags"]
    sources = load_sources()
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    codes = select_codes(args.codes, flags)
    report = Report()
    for code in codes:
        check_flag(code, sources, flags, readme, report)
    for code in sorted(set(sources) - set(flags)):
        report.error("sources.json", f"has a record for {code}, which has no recipe")
    check_exclusions(data, report)
    check_notice(flags, sources, report)
    if args.render:
        check_renders([c for c in codes if (REPO / "full-size" / "states" / f"{c}.svg").exists()], flags, report)
    if args.repo:
        ours = {REPO / v / "states" / f"{c}.svg" for v in VARIANTS for c in flags}
        for variant in VARIANTS:
            for path in sorted((REPO / variant).rglob("*.svg")):
                if path not in ours:
                    structural(path, report, strict=False)

    for line in report.warnings:
        print(f"warning: {line}")
    for line in report.errors:
        print(f"error: {line}")
    print(f"{len(codes)} flags checked: {len(report.errors)} errors, {len(report.warnings)} warnings")
    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
