# svg-flags

Clean, Xcode-compatible SVG flags with official colors in multiple shapes.

**[Browse the gallery](https://motomatic-llc.github.io/svg-flags)**

## Why this exists

I use [HatScripts/circle-flags](https://github.com/HatScripts/circle-flags) in many different projects — it's a fantastic collection of 400+ minimal circular SVG flags. But I keep running into the same issues:

**Xcode can't render them.** The circle-flags SVGs use `<mask>` elements for circular clipping. Xcode's SVG renderer has limited support — it doesn't handle masks, CSS `<style>` blocks, or complex filters. Importing these into an Xcode asset catalog produces blank or broken images. This project uses `<clipPath>` instead, which Xcode handles correctly.

**Circle shape isn't always enough.** Circular flags work great for profile badges and map markers, but many UI contexts call for rectangular flags — table rows, settings screens, country pickers, informational displays. This project provides multiple shape variants from simplified icons to full-detail flags.

**Colors are simplified.** circle-flags maps every flag to an 11-color palette for visual consistency. That's a reasonable design choice, but it means the US flag uses `#d80027` instead of Old Glory Red `#B31942`, and `#0052b4` instead of Old Glory Blue `#0A3161`. This project uses the actual official flag colors, sourced from Wikipedia/Wikimedia Commons SVGs, and documents every color in `colors.csv`.

**Symlinks cause problems.** The language flags in circle-flags are symlinks pointing to country flags. Symlinks break in Xcode asset catalogs, some npm packaging, and cross-platform workflows. This project duplicates files instead — every flag is a standalone SVG.

## Credits

This project is based on and inspired by [HatScripts/circle-flags](https://github.com/HatScripts/circle-flags), which is MIT licensed. The SVG geometry for circle and rect variants was adapted from that project, with modifications for Xcode compatibility and official color accuracy. Full-size variants are based on Wikimedia Commons SVGs.

## Variants

| Variant | Directory | Source | Description |
|---------|-----------|--------|-------------|
| Circle | `circle/` | circle-flags | 512×512 circular flags, `<mask>` → `<clipPath>`, real colors |
| Rect | `rect/` | circle-flags | 512×512 square, circle-flags geometry without circular clip |
| Full-size simplified | `full-size-simplified/` | circle-flags | True aspect ratio, simplified geometry for complicated flags, real colors |
| Full-size | `full-size/` | Wikipedia | True proportions & detail, based on Wikimedia Commons SVGs |

**circle** and **rect** use the same simplified geometry from circle-flags — just with official colors and Xcode-compatible SVG elements. **full-size-simplified** uses that geometry at the flag's true aspect ratio. **full-size** uses the actual detailed flag SVGs from Wikipedia with proper proportions and accurate geometry.

## Border

Circle and rect variants of mostly-white flags (like Japan) include a subtle grey border (<img src="swatches/eaecf0.svg" width="12"> `#eaecf0`) to prevent them from disappearing into white backgrounds.

The border is the last element in the SVG, marked with a `<!-- border -->` comment:

```xml
<!-- border --><circle cx="256" cy="256" r="250" fill="none" stroke="#eaecf0" stroke-width="12"/>
```

To remove it, delete the line or strip all borders with:

```bash
sed -i '' '/<!-- border -->/d' circle/**/*.svg rect/**/*.svg
```

## Structure

```
svg-flags/
├── circle/
│   ├── countries/     # UN member states (ISO 3166-1 alpha-2)
│   ├── other/
│   │   ├── locales/   # Non-UN places (tw.svg, northern-cyprus.svg, ...)
│   │   └── orgs/      # Organizations & symbols (nato.svg, un.svg, ...)
│   ├── historical/    # Former states (confederacy.svg, ussr.svg, ...)
│   ├── states/        # Subdivisions (us/ca.svg, us/ny.svg, ...)
│   └── languages/     # Language codes (en.svg, es.svg, ...)
├── rect/
│   └── (same subcategories)
├── full-size-simplified/
│   └── (same subcategories)
├── full-size/
│   └── (same subcategories)
├── colors.csv         # Color reference with official sources
└── index.html       # Visual gallery (open in browser)
```

## Categories

- **countries/** — UN member states, using [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) codes
- **other/** — Two subcategories:
  - **other/locales/** — Places with widely recognized flags that are not UN member states (e.g. Taiwan, Northern Cyprus, Kosovo)
  - **other/orgs/** — Organizations, symbols, and novelty flags (e.g. NATO, UN, Olympics, checkered flag, pirate flag)
- **historical/** — Flags of former states and defunct entities (e.g. Confederate States, Soviet Union, Prussia)
- **states/** — Subnational divisions (e.g. US states, Canadian provinces), using [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) codes
- **languages/** — Language flags (duplicated files, not symlinks)

## Progress

### Countries (UN member states)

| | Code | Name | Circle | Rect | Simplified | Full-size |
|:-:|------|------|:------:|:----:|:----------:|:---------:|
| <img src="circle/countries/us.svg" width="24"> | `us` | United States | ✓ | ✓ | ✓ | ✓ |
| <img src="circle/countries/gb.svg" width="24"> | `gb` | United Kingdom | ✓ | ✓ | ✓ | ✓ |
| <img src="circle/countries/fr.svg" width="24"> | `fr` | France | ✓ | ✓ | ✓ | ✓ |
| <img src="circle/countries/de.svg" width="24"> | `de` | Germany | ✓ | ✓ | ✓ | ✓ |
| <img src="circle/countries/jp.svg" width="24"> | `jp` | Japan | ✓ | ✓ | ✓ | ✓ |
| | `ca` | Canada | | | | |
| | `au` | Australia | | | | |
| | `br` | Brazil | | | | |
| | `cn` | China | | | | |
| | `in` | India | | | | |
| | `it` | Italy | | | | |
| | `mx` | Mexico | | | | |
| | `kr` | South Korea | | | | |
| | `es` | Spain | | | | |
| | `se` | Sweden | | | | |
| | `no` | Norway | | | | |
| | `nl` | Netherlands | | | | |
| | `pt` | Portugal | | | | |
| | `ru` | Russia | | | | |
| | `ie` | Ireland | | | | |
| | `ch` | Switzerland | | | | |
| | `pl` | Poland | | | | |
| | `ar` | Argentina | | | | |
| | `za` | South Africa | | | | |
| | `nz` | New Zealand | | | | |

### Other locales (non-UN entities)

| | Code | Name | Circle | Rect | Simplified | Full-size |
|:-:|------|------|:------:|:----:|:----------:|:---------:|
| | `tw` | Taiwan | | | | |
| | `xk` | Kosovo | | | | |
| | `northern-cyprus` | Northern Cyprus | | | | |

### Organizations & symbols

| | Code | Name | Circle | Rect | Simplified | Full-size |
|:-:|------|------|:------:|:----:|:----------:|:---------:|
| | `nato` | NATO | | | | |
| | `un` | United Nations | | | | |
| | `olympics` | Olympics | | | | |
| | `checkered` | Checkered flag | | | | |
| | `pirate` | Pirate flag | | | | |

### Historical

| | Code | Name | Circle | Rect | Simplified | Full-size |
|:-:|------|------|:------:|:----:|:----------:|:---------:|
| <img src="circle/historical/confederacy.svg" width="24"> | `confederacy` | Confederate States | ✓ | ✓ | ✓ | ✓ |

## SVG Design Rules

All SVGs in this project follow these rules for maximum compatibility:

- No `<mask>` elements (Xcode doesn't support them)
- No `<style>` tags or CSS
- No `class` attributes
- No `<use>` / `xlink:href` references (Xcode has inconsistent support)
- No symlinks — every file is standalone
- Circle variants use `<clipPath>` with `<circle>` for clipping
- All styling via inline `fill` attributes
- `viewBox`-based sizing for clean scaling
- Official flag colors sourced from Wikipedia/Wikimedia Commons

## Color Sources

Every color is documented in `colors.csv` with a source URL. We prefer Wikipedia/Wikimedia Commons SVGs as the primary color reference:

- **US:** [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Flag_of_the_United_States.svg) — <img src="swatches/B31942.svg" width="12"> `#B31942` (Old Glory Red), <img src="swatches/0A3161.svg" width="12"> `#0A3161` (Old Glory Blue)
- **UK:** [Wikipedia](https://en.wikipedia.org/wiki/File:Flag_of_the_United_Kingdom.svg) — <img src="swatches/C8102E.svg" width="12"> `#C8102E` (red), <img src="swatches/012169.svg" width="12"> `#012169` (blue)
- **France:** [Wikipedia](https://en.wikipedia.org/wiki/File:Flag_of_France.svg) — <img src="swatches/002654.svg" width="12"> `#002654` (blue), <img src="swatches/CE1126.svg" width="12"> `#CE1126` (red)
- **Germany:** [Wikipedia](https://en.wikipedia.org/wiki/File:Flag_of_Germany.svg) — <img src="swatches/000000.svg" width="12"> `#000000` (black), <img src="swatches/DD0000.svg" width="12"> `#DD0000` (red), <img src="swatches/FFCE00.svg" width="12"> `#FFCE00` (gold)
- **Japan:** [Wikipedia](https://en.wikipedia.org/wiki/File:Flag_of_Japan.svg) — <img src="swatches/BC002D.svg" width="12"> `#BC002D` (red)
- **Confederacy:** [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Battle_flag_of_the_Confederate_States_of_America_(3-5).svg) — <img src="swatches/bf0a30.svg" width="12"> `#bf0a30` (red), <img src="swatches/002868.svg" width="12"> `#002868` (blue)

## Usage

### Xcode Asset Catalog

Drag any SVG directly into your asset catalog. Works out of the box — no conversion needed.

### SwiftUI

```swift
Image("us") // after adding to asset catalog
```

### HTML

```html
<img src="svg-flags/rect/countries/us.svg" alt="United States" width="30">
```

## License

MIT — see [LICENSE](LICENSE). Based on [circle-flags](https://github.com/HatScripts/circle-flags) by HatScripts.
