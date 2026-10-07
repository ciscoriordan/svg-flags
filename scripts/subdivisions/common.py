"""Shared paths and helpers for the subdivision flag pipeline.

The pipeline turns Wikimedia Commons artwork into the four variants this repo
ships (circle, square, full-size, full-size-simplified). Every step reads the
hand-maintained recipe file (flags.json) and the generated source lock
(sources.json), so re-running the steps reproduces the committed SVGs.
"""

import io
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CACHE = REPO / ".cache" / "subdivisions"
FLAGS_JSON = HERE / "flags.json"
SOURCES_JSON = HERE / "sources.json"
VARIANTS = ("circle", "square", "full-size-simplified", "full-size")

# Wikimedia asks API clients to identify themselves. The contact is the public
# repository, not a person.
USER_AGENT = "svg-flags-subdivisions/1.0 (https://github.com/ciscoriordan/svg-flags)"


def load_flags():
    return json.loads(FLAGS_JSON.read_text(encoding="utf-8"))


def load_sources():
    if not SOURCES_JSON.exists():
        sys.exit(f"{SOURCES_JSON.relative_to(REPO)} is missing; run lock_sources.py first")
    return json.loads(SOURCES_JSON.read_text(encoding="utf-8"))


def write_json(path, data):
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def select_codes(args, available):
    """Filter codes by command-line arguments.

    An argument is either a full code ("ca-on") or a country prefix ("ca").
    With no arguments every available code is selected.
    """
    available = sorted(available)
    if not args:
        return available
    picked = []
    for arg in args:
        arg = arg.lower()
        matches = [c for c in available if c == arg or c.split("-")[0] == arg]
        if not matches:
            sys.exit(f"no flag matches {arg!r}")
        picked.extend(m for m in matches if m not in picked)
    return sorted(picked)


def http_get(url, attempts=5):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except Exception:
            if attempt == attempts - 1:
                raise
            # Wikimedia throttles bursts; back off instead of failing the run.
            time.sleep(2 + attempt * 3)


def render(svg, width, height=None):
    """Render SVG bytes or a path with rsvg-convert and return an RGBA image."""
    from PIL import Image

    cmd = ["rsvg-convert", "-w", str(width)]
    if height is not None:
        cmd += ["-h", str(height)]
    if isinstance(svg, (str, Path)):
        cmd.append(str(svg))
        data = None
    else:
        data = svg
    result = subprocess.run(cmd, input=data, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"rsvg-convert failed: {result.stderr.decode(errors='replace').strip()}")
    return Image.open(io.BytesIO(result.stdout)).convert("RGBA")


# Fidelity checks render at this width (for landscape flags; portrait flags
# use it as the height), where a flag's smallest charges are several pixels
# across, so losing or reshaping one shows up as a block of changed pixels.
CHECK_SIZE = 1200
# A pixel "changes" when any channel moves by more than this many levels.
# Moving an edge by a fraction of a pixel only shifts antialiasing by a few
# levels, so rounding alone stays below it.
CHANGE_LEVELS = 40
# How far a cleaned full-size flag may drift from its Commons original: the
# share of pixels that change, and the largest connected group of changed
# pixels. A missing or reshaped element is one solid group (a billet of the
# Northwest Territories shield is about 450 pixels at the check size, and the
# smallest such defect found so far was 72), while rounding leaves isolated
# pixels along edges.
MAX_DRIFT_SHARE = 0.0002
MAX_DRIFT_REGION = 24


def drift_limits(recipe):
    """(share, region) limits for a flag.

    A recipe that changes the artwork on purpose (flattening raster patches,
    dropping blurred shading) states its own limits with the reason, under
    "clean": {"max_drift": [share, region], "why": "..."}.
    """
    limits = recipe.get("clean", {}).get("max_drift")
    return tuple(limits) if limits else (MAX_DRIFT_SHARE, MAX_DRIFT_REGION)


def check_dimensions(svg_path):
    """Pixel size for comparing renders of a flag, from its width and height."""
    from lxml import etree

    root = etree.parse(str(svg_path)).getroot()
    return check_size(float(root.get("width")), float(root.get("height")))


def check_size(width, height):
    if width >= height:
        return CHECK_SIZE, round(CHECK_SIZE * height / width)
    return round(CHECK_SIZE * width / height), CHECK_SIZE


def original_view(cleaned_path, recipe):
    """The cleaned full-size flag as SVG bytes, showing only the area of its
    Commons original.

    A recipe's "canvas" option extends the field beyond the original drawing
    (see clean.py); the fidelity check compares only the part that came from
    Commons.
    """
    from lxml import etree

    data = Path(cleaned_path).read_bytes()
    canvas = recipe.get("canvas")
    if not canvas:
        return data
    root = etree.fromstring(data)
    left, top, right, bottom = canvas["extend"]
    x, y, w, h = (float(v) for v in root.get("viewBox").split())
    scale = float(root.get("width")) / w
    box = [x + left, y + top, w - left - right, h - top - bottom]
    root.set("viewBox", " ".join(f"{v:g}" for v in box))
    root.set("width", f"{box[2] * scale:g}")
    root.set("height", f"{box[3] * scale:g}")
    return etree.tostring(root)


def fidelity(original_path, cleaned_path, recipe):
    """(share, region) by which a cleaned full-size flag differs from its
    Commons original, compared at the check size (see compare_renders)."""
    from lxml import etree

    view = original_view(cleaned_path, recipe)
    root = etree.fromstring(view)
    size = check_size(float(root.get("width")), float(root.get("height")))
    a, b = render(original_path, *size), render(view, *size)
    if recipe.get("canvas"):
        # The canvas fills reach a little under the artwork so that no seam
        # opens where they meet it, which also makes the original's
        # antialiased edge opaque. Leave out that one pixel line on every
        # side the canvas extends.
        left, top, right, bottom = (1 if v > 0 else 0 for v in recipe["canvas"]["extend"])
        box = (left, top, size[0] - right, size[1] - bottom)
        a, b = a.crop(box), b.crop(box)
    return compare_renders(a, b)


def compare_renders(a, b):
    """Compare two renders of the same size.

    Returns (share, region): the share of pixels that changed, and the size
    in pixels of the largest 8-connected group of changed pixels. The region
    is what catches a missing or reshaped element: a dropped charge is one
    solid block, while rounding scatters isolated pixels along edges.
    """
    from PIL import ImageChops

    bands = ImageChops.difference(a, b).split()
    worst = bands[0]
    for band in bands[1:]:
        worst = ImageChops.lighter(worst, band)
    mask = worst.point(lambda v: 255 if v > CHANGE_LEVELS else 0)
    changed = mask.histogram()[255]
    if not changed:
        return 0.0, 0
    width = mask.width
    data = mask.tobytes()
    pending = {i for i, v in enumerate(data) if v}
    largest = 0
    while pending:
        stack = [pending.pop()]
        size = 0
        while stack:
            i = stack.pop()
            size += 1
            x, y = i % width, i // width
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx or dy:
                        n = (y + dy) * width + x + dx
                        if 0 <= x + dx < width and n in pending:
                            pending.remove(n)
                            stack.append(n)
        largest = max(largest, size)
    return changed / (a.width * a.height), largest


def flatten(image, background=(255, 255, 255)):
    """Composite an RGBA image over a solid background and return RGB."""
    from PIL import Image

    base = Image.new("RGBA", image.size, background + (255,))
    base.alpha_composite(image)
    return base.convert("RGB")


def run_svgo(jobs):
    """Run svgo_run.mjs over [{"in", "out", "pass", "precision"}] jobs."""
    result = subprocess.run(["node", str(HERE / "svgo_run.mjs")], input=json.dumps(jobs).encode(),
                            capture_output=True, cwd=HERE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())


def cleaned_path(code):
    """Cleaned full-size art, the input every other variant is built from."""
    return REPO / "full-size" / "states" / f"{code}.svg"


def commons_cache_path(code):
    return CACHE / "commons" / f"{code}.svg"


def coresvg_render(jobs):
    """Render [(svg_path, png_path, width, height)] with CoreSVG (macOS only).

    Returns the set of SVG paths CoreSVG could not load. The helper binary is
    compiled once into the cache from coresvg_render.swift.
    """
    binary = CACHE / "bin" / "coresvg_render"
    source = HERE / "coresvg_render.swift"
    if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
        binary.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swiftc", "-O", "-o", str(binary), str(source)], check=True)
    lines = "".join(f"{svg}\t{png}\t{w}\t{h}\n" for svg, png, w, h in jobs)
    result = subprocess.run([str(binary)], input=lines.encode(), capture_output=True, check=True)
    return {line.split(" ", 1)[1] for line in result.stdout.decode().splitlines() if line.startswith("fail ")}


def coresvg_available():
    return sys.platform == "darwin" and shutil.which("swiftc") is not None
