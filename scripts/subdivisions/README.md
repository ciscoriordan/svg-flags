# Subdivision flag pipeline

These scripts build the subdivision flags of Argentina, Brazil, Canada, Mexico, Spain and Switzerland in all four variants from Wikimedia Commons artwork. Every decision that used to be a hand edit (which Commons file, which crop, how far to zoom, whether to add the grey border) is data in `flags.json`, so the SVGs can be rebuilt at any time and come out the same.

## Files

| File | Edited by | Purpose |
|------|-----------|---------|
| `flags.json` | hand | One recipe per flag: name, Commons file, cleaning options, layout of the circle and square variants, and the notes the credits and license review need (`adaptation`, `later_versions`). Also the country headings for the README and the codes that are left out on purpose, with the reason (`excluded`; at present the Mexican states that have no official flag). |
| `sources.json` | `lock_sources.py` | The pinned Commons revision (SHA-1) of each file and the uploads it descends from, the license it is distributed under with the license tags and source files that was worked out from, the author as the file page names them, the other uploaders a credit names, and the English Wikipedia article for the region (found on Wikidata through its ISO 3166-2 code). |
| `lock_sources.py` | | Pins sources and records their licenses and authors (see Licenses below). |
| `commons_license.py` | | Works out the license a Commons file can be redistributed under from all of its license tags and from the files it was drawn from. |
| `commons_author.py` | | Reads a file's author from the Author field of its page (falling back to the name in its public-domain release, then to its first uploader). |
| `fetch.py` | | Downloads the pinned revisions into `.cache/subdivisions/commons/` and checks their SHA-1. |
| `clean.py` | | Turns each Commons SVG into `full-size/states/<code>.svg` (copied to `full-size-simplified/`). |
| `build_variants.py` | | Composes `circle/states/<code>.svg` and `square/states/<code>.svg` from the cleaned art. Its docstring describes the layout options. |
| `measure.py` | | Prints where an emblem sits on a flag, in the units the layout options use. |
| `contact_sheet.py` | | Renders review sheets into `.cache/subdivisions/sheets/`. |
| `render_docs.py` | | Writes the README tables, the README credits, `NOTICE.md` (the files that are not MIT), the gallery sections and any missing swatch files. |
| `validate.py` | | Checks the result (see below). |

## Licenses

A license never decides whether a flag is included, only how it is credited. Where an equally faithful public-domain or CC0 drawing of the current design exists, the recipe uses it (Lucerne); otherwise it uses the file Wikidata or the English Wikipedia article on the flag shows, whatever its license.

Commons reports one license per file, which is simply the first license tag on the page. Flag files usually carry a public-domain tag for the design (an official flag or coat of arms) next to the license the person who drew the SVG chose for the drawing, so that first tag can say "public domain" for a drawing that is GFDL or CC BY. `lock_sources.py` therefore reads every tag through `commons_license.py`:

- the license categories of the file page, which every license template adds, including ones inside user templates;
- the licenses inside each `{{self}}`, `{{self2}}` or `{{GFDL-self}}` template (`{{GFDL-self|migration=relicense}}` also grants CC BY-SA 3.0);
- user templates that ask for attribution in prose, such as `{{User:Heraldry/Attribution}}`;
- the files the drawing was built from (`{{Attrib}}`, `{{AttribSVG}}`, `{{Own based}}`, `{{Derived from}}` and file links in the Source field).

The licenses on one page are alternatives (Commons treats such a file as multi-licensed), so the most permissive one is picked, a Creative Commons license before the GFDL, newest version first: `{{self|cc-by-sa-3.0|GFDL}}` becomes CC BY-SA 3.0. Design-level public-domain tags (PD-BrazilGov, PD-Coa-Mexico, PD-old, PD-ineligible and the like) do not license the drawing, so they only decide when nothing else is tagged. The licenses of the files a drawing was built from hold as well, unless the drawing is tagged as too simple for copyright or its author released it and built it from their own earlier work.

A file page's Author field usually describes the first upload, while the pinned revision may have been redrawn by others since. `lock_sources.py` therefore reads the upload history and records the uploads the pinned revision descends from (a revert continues from the bytes it restores); a credit names every uploader in that ancestry whom the Author field does not already name. A public-domain release or CC0 dedication by one person (`{{PD-self}}`, `{{PD-user|Name}}`, `{{PD-author|Name}}`, `{{self|cc-zero}}`) covers only that person's work:

- If others contributed to the pinned drawing and the page also offers a public license such as CC BY, that license is used and the contributors are credited (Paraná: FXXX released the 2008 drawing, while the pinned one was redrawn by JPedroBrazil and SVG flag maker, so the page's CC BY 2.5 applies).
- If the page offers nothing else, the recipe's `later_versions` says what the other uploads changed, after a look at the file history, and `lock_sources.py` stops until it does. Commons does not let a new version change a file's license, so those uploads were published under the same release; the note records whether they redrew anything.

The result is recorded in `sources.json` as one of three kinds:

- public domain (including CC0): no credit needed; the files are MIT like the rest of the repository.
- attribution (CC BY, or the author's own request for credit): `render_docs.py` writes a credit entry into the README's Credits section, naming the subdivision and code, the Commons file, its author and license, and any source file whose license also holds.
- share-alike (CC BY-SA): credited the same way, and the entry says that the four files of that code are distributed under that license instead of MIT.

Each credit entry also says how the files differ from the drawing: what the full-size files change on purpose (the `clean` and `canvas` options), and whether the circle and square files are crops, zoomed-out views with the field continued, or recompositions. A recipe's `adaptation` text replaces that last part where the generic wording would hide something, such as a border that the circle leaves out.

`render_docs.py` writes the same entries, with the paths of the four files, into `NOTICE.md` at the root of the repository, and `LICENSE` excludes the files listed there from the MIT license. `validate.py` checks that every credit entry is in the README, that `NOTICE.md` is current and that `LICENSE` points to it. `lock_sources.py` stops when a file has no license tag, is offered only under the GFDL, names no author (or an author that reads like license boilerplate), or needs a `later_versions` note that its recipe lacks. Apps that show credited flags have to credit the authors too.

## Setup

Requires `rsvg-convert` (Homebrew: `brew install librsvg`), Node.js, and Python 3. The CoreSVG checks also need macOS with Xcode command line tools.

```bash
cd scripts/subdivisions
npm ci
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Rebuilding

Run from `scripts/subdivisions`. Every script takes optional codes or country prefixes (`ca-on`, `ch`).

```bash
.venv/bin/python fetch.py
.venv/bin/python clean.py
.venv/bin/python build_variants.py
.venv/bin/python contact_sheet.py      # then look at .cache/subdivisions/sheets/*.png
.venv/bin/python render_docs.py
.venv/bin/python validate.py --render
(cd ../.. && python3 validate-swatches.py)
```

## Adding a flag

1. Add a recipe to `flags.json` with the name and the exact Commons file name. Prefer the file that Wikidata lists as the region's flag (property P41) unless it is not the current official design, or an equally faithful public-domain drawing exists. If the drawing's proportions differ from the ones the flag's law gives, restore them with `"canvas"` (see `clean.py`) and say why.
2. Run `lock_sources.py`, then `fetch.py` and `clean.py` for the new code. `clean.py` reports how far the cleaned file drifts from the Commons original; if it marks the flag, find out why before going on.
3. Choose a layout. `measure.py` gives the numbers for `"fit"` and `"layers"`. Lettering must end up wholly inside or wholly outside the circle, never cut mid-word. Build with `build_variants.py` and check the contact sheet at 96 and 24 pixels, on light and dark backgrounds. Where the artwork ends inside the frame, add `"covers"` if `validate.py --render` reports a seam.
4. Run `render_docs.py` and `validate.py --render`.

Do not edit the generated SVGs or `sources.json` by hand; change the recipe or the scripts and rebuild. When Commons replaces a file, `lock_sources.py` keeps the old pin and says so; review the new artwork, then re-pin it with `lock_sources.py --refresh CODE`.

## What validate.py checks

- No `<mask>`, `<style>`, `class`, `<use>`, `href`, `<image>`, `<text>`, `<filter>` or `<marker>`, and no symlinks.
- A viewBox everywhere; circle and square are 512x512 with their content in one group clipped by the 512 circle or square.
- Every `url(#id)` resolves to exactly one element; no duplicate ids.
- The border, where present, is written exactly as the main README shows it, since the border strippers match that text.
- Uppercase 6-digit hex colors; circle and square use only colors of the full-size flag.
- A pinned source with a known license and an author for every flag, and the README credit entry for every flag whose license asks for credit.
- No files for codes listed under `excluded`.
- `NOTICE.md` is exactly what `render_docs.py` writes, and `LICENSE` points to it.
- Size: circle and square warn above 100 KB and fail above 238 KB (the largest flag that predates the pipeline), with documented exceptions.
- With `--render`:
  - the full-size file matches the Commons original at 1200 pixels: at most 0.02% of pixels move by more than 40 levels, and no connected patch of changed pixels is larger than 24 pixels, so a missing or reshaped element fails even when it is small. A recipe that changes the artwork on purpose (`"clean": {"flatten_images": true}` for embedded raster shading, `"drop_blurred": true` for blurred shadows CoreSVG cannot draw) states its own limits and the reason; with `"canvas"`, only the area of the original is compared;
  - no seams in circle and square: along every line where the artwork ends inside the frame, a render at 44 to 132 pixels is compared with an 8x supersampled one, and a run of three or more pixels that differ marks a seam;
  - on macOS, CoreSVG draws every variant like rsvg does (at most 1% of pixels differ).
- With `--repo`: the structural rules over every other SVG in the repo, reported as warnings.

## Publishing

jsDelivr caches `@main` for hours, including 404 responses for files that did not exist yet. After pushing new flags, purge each new path, for example `https://purge.jsdelivr.net/gh/ciscoriordan/svg-flags@main/circle/states/ca-on.svg`, and check that the CDN URL returns 200.
