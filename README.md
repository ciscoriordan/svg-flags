# svg-flags

Clean, Xcode-compatible SVG flags with official colors in multiple shapes.

**[Browse the gallery](https://ciscoriordan.github.io/svg-flags)**

## Table of contents

- [Why this exists](#why-this-exists)
- [Credits](#credits)
- [Variants](#variants)
- [Xcode compatibility](#xcode-compatibility)
- [Border](#border)
- [Structure](#structure)
- [Categories](#categories)
- [Progress](#progress)
  - [Countries (UN member states)](#countries-un-member-states)
  - [Languages](#languages)
  - [Other locales (non-UN entities)](#other-locales-non-un-entities)
  - [Organizations & symbols](#organizations--symbols)
  - [Subdivisions (ISO 3166-2)](#subdivisions-iso-3166-2)
  - [Historical](#historical)
- [SVG Design Rules](#svg-design-rules)
- [Usage](#usage)
- [License](#license)

## Why this exists

I use [HatScripts/circle-flags](https://github.com/HatScripts/circle-flags) in many different projects — it's a fantastic collection of 400+ minimal circular SVG flags. But I keep running into the same issues:

**Xcode can't render them.** The circle-flags SVGs use `<mask>` elements for circular clipping. Xcode's SVG renderer has limited support — it doesn't handle masks, CSS `<style>` blocks, or complex filters. Importing these into an Xcode asset catalog produces blank or broken images. This project uses `<clipPath>` instead, which Xcode handles correctly.

**Circle shape isn't always enough.** Circular flags work great for profile badges and map markers, but many UI contexts call for rectangular flags — table rows, settings screens, country pickers, informational displays. This project provides multiple shape variants from simplified icons to full-detail flags.

**Colors are simplified.** circle-flags maps every flag to an 11-color palette for visual consistency. That's a reasonable design choice, but it means the US flag uses <img src="swatches/d80027.svg" width="12">`#d80027` instead of Old Glory Red <img src="swatches/B31942.svg" width="12">`#B31942`, and <img src="swatches/0052b4.svg" width="12">`#0052b4` instead of Old Glory Blue <img src="swatches/0A3161.svg" width="12">`#0A3161`. This project uses the actual official flag colors, sourced from Wikipedia/Wikimedia Commons SVGs, and documents every color below.

| svg-flags | circle-flags |
|:---:|:---:|
| <img src="circle/countries/us.svg" width="96"> | <img src="comparison/circle-flags-us.svg" width="96"> |
| Official colors ![NEW](https://img.shields.io/badge/NEW-2ea44f) | Simplified palette ![OLD](https://img.shields.io/badge/OLD-gray) |

**Symlinks cause problems.** The language flags in circle-flags are symlinks pointing to country flags. Symlinks break in Xcode asset catalogs, some npm packaging, and cross-platform workflows. This project duplicates files instead — every flag is a standalone SVG.

## Credits

This project is based on and inspired by [HatScripts/circle-flags](https://github.com/HatScripts/circle-flags), which is MIT licensed. Circle variant geometry was adapted from that project, with `<mask>` replaced by `<clipPath>` for Xcode compatibility and official colors replacing the simplified palette. Square variant geometry comes from [kapowaz/square-flags](https://github.com/kapowaz/square-flags), again with official Wikipedia colors. Full-size variants are based on Wikimedia Commons SVGs.

## Variants

| Variant | Directory | Source | Description |
|---------|-----------|--------|-------------|
| Circle | `circle/` | circle-flags | 512×512 circular flags, `<mask>` → `<clipPath>`, real colors |
| Square | `square/` | square-flags | 512×512 square, square-flags geometry with official colors |
| Full-size simplified | `full-size-simplified/` | square-flags | True aspect ratio, simplified geometry for complicated flags, real colors |
| Full-size | `full-size/` | Wikipedia | True proportions & detail, based on Wikimedia Commons SVGs |

**circle** uses simplified geometry from circle-flags, **square** and **full-size-simplified** use geometry from square-flags — all with official Wikipedia colors and Xcode-compatible SVG elements. **full-size** uses the actual detailed flag SVGs from Wikimedia Commons with proper proportions and accurate geometry.

## Xcode compatibility

Xcode's SVG renderer has limited support compared to browsers. These SVGs are cleaned to avoid elements Xcode can't handle:

- **No `<mask>`** — replaced with `<clipPath>` (circle and square variants)
- **No `<style>` or CSS** — all styling uses inline `fill`/`stroke` attributes
- **No `<use>` or `xlink:href`** — Wikimedia SVGs often define a shape once (e.g. a star) in `<defs>` and then reference it multiple times with `<use xlink:href="#id" x="..." y="..." transform="...">`. Xcode doesn't support `<use>`, so every instance is expanded into an inline copy with the correct `transform="translate(x,y)"` or `transform="rotate(N)"`. Recursive `<use>` patterns (where elements reference other compound elements to build up star rings, sun rays, wheel spokes, etc.) are fully unrolled.
- **No symlinks** — language flags are duplicated files, not symlinks

## Border

Circle and square variants of mostly-white flags (like Japan) include a subtle grey border (<img src="swatches/cdcfd3.svg" width="12">`#cdcfd3`) to prevent them from disappearing into white backgrounds.

The border is inside the `<clipPath>` group so only the inner half of the stroke is visible — the flag stays full-size. It's marked with a `<!-- border -->` comment:

```xml
<!-- border --><circle cx="256" cy="256" r="256" fill="none" stroke="#cdcfd3" stroke-width="4"/>
```

To remove it, delete the line or strip all borders with:

```bash
sed -i '' '/<!-- border -->/d' circle/**/*.svg square/**/*.svg
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
│   ├── states/        # Subdivisions (us-ca.svg, us-ny.svg, ...)
│   └── languages/     # Language codes (en.svg, es.svg, ...)
├── square/
│   └── (same subcategories)
├── full-size-simplified/
│   └── (same subcategories)
├── full-size/
│   └── (same subcategories)
└── index.html         # Visual gallery (open in browser)
```

## Categories

- **countries/** — UN member states, using [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) codes
- **other/** — Two subcategories:
  - **other/locales/** — Places with widely recognized flags that are not UN member states (e.g. Taiwan, Northern Cyprus, Kosovo)
  - **other/orgs/** — Organizations, symbols, and novelty flags (e.g. NATO, UN, Olympics, F1 chequered flag)
- **historical/** — Flags of former states and defunct entities (e.g. Confederate battle flag, Soviet Union, Prussia)
- **states/** — Subdivisions ([ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2)), grouped by country code prefix (e.g. `ca-bc`, `us-ca`)
- **languages/** — Language flags (duplicated files, not symlinks)

## Progress

### Countries (UN member states)

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `fr` | [France](https://en.wikipedia.org/wiki/France) | <img src="circle/countries/fr.svg" width="32"> | <img src="square/countries/fr.svg" width="32"> | <img src="full-size-simplified/countries/fr.svg" height="20"> | [✓](full-size/countries/fr.svg) | [<img src="swatches/002654.svg" width="12">`#002654`](https://en.wikipedia.org/wiki/File:Flag_of_France.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_France.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://en.wikipedia.org/wiki/File:Flag_of_France.svg) |
| `gr` | [Greece](https://en.wikipedia.org/wiki/Greece) | <img src="circle/countries/gr.svg" width="32"> | <img src="square/countries/gr.svg" width="32"> | <img src="full-size-simplified/countries/gr.svg" height="20"> | [✓](full-size/countries/gr.svg) | [<img src="swatches/0D5EAF.svg" width="12">`#0D5EAF`](https://en.wikipedia.org/wiki/File:Flag_of_Greece.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Greece.svg) |
| `de` | [Germany](https://en.wikipedia.org/wiki/Germany) | <img src="circle/countries/de.svg" width="32"> | <img src="square/countries/de.svg" width="32"> | <img src="full-size-simplified/countries/de.svg" height="20"> | [✓](full-size/countries/de.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://en.wikipedia.org/wiki/File:Flag_of_Germany.svg)<br>[<img src="swatches/DD0000.svg" width="12">`#DD0000`](https://en.wikipedia.org/wiki/File:Flag_of_Germany.svg)<br>[<img src="swatches/FFCE00.svg" width="12">`#FFCE00`](https://en.wikipedia.org/wiki/File:Flag_of_Germany.svg) |
| `jp` | [Japan](https://en.wikipedia.org/wiki/Japan) | <img src="circle/countries/jp.svg" width="32"> | <img src="square/countries/jp.svg" width="32"> | <img src="full-size-simplified/countries/jp.svg" height="20"> | [✓](full-size/countries/jp.svg) | [<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Japan.svg)<br>[<img src="swatches/BC002D.svg" width="12">`#BC002D`](https://en.wikipedia.org/wiki/File:Flag_of_Japan.svg) |
| `ke` | [Kenya](https://en.wikipedia.org/wiki/Kenya) | <img src="circle/countries/ke.svg" width="32"> | <img src="square/countries/ke.svg" width="32"> | <img src="full-size-simplified/countries/ke.svg" height="20"> | [✓](full-size/countries/ke.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://en.wikipedia.org/wiki/File:Flag_of_Kenya.svg)<br>[<img src="swatches/BB0000.svg" width="12">`#BB0000`](https://en.wikipedia.org/wiki/File:Flag_of_Kenya.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Kenya.svg)<br>[<img src="swatches/006600.svg" width="12">`#006600`](https://en.wikipedia.org/wiki/File:Flag_of_Kenya.svg) |
| `gb` | [United Kingdom](https://en.wikipedia.org/wiki/United_Kingdom) | <img src="circle/countries/gb.svg" width="32"> | <img src="square/countries/gb.svg" width="32"> | <img src="full-size-simplified/countries/gb.svg" height="20"> | [✓](full-size/countries/gb.svg) | [<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://en.wikipedia.org/wiki/File:Flag_of_the_United_Kingdom.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_the_United_Kingdom.svg)<br>[<img src="swatches/012169.svg" width="12">`#012169`](https://en.wikipedia.org/wiki/File:Flag_of_the_United_Kingdom.svg) |
| `us` | [United States](https://en.wikipedia.org/wiki/United_States) | <img src="circle/countries/us.svg" width="32"> | <img src="square/countries/us.svg" width="32"> | <img src="full-size-simplified/countries/us.svg" height="20"> | [✓](full-size/countries/us.svg) | [<img src="swatches/B31942.svg" width="12">`#B31942`](https://commons.wikimedia.org/wiki/File:Flag_of_the_United_States.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_United_States.svg)<br>[<img src="swatches/0A3161.svg" width="12">`#0A3161`](https://commons.wikimedia.org/wiki/File:Flag_of_the_United_States.svg) |
| `af` | [Afghanistan](https://en.wikipedia.org/wiki/Afghanistan) | <img src="circle/countries/af.svg" width="32"> | <img src="square/countries/af.svg" width="32"> | <img src="full-size-simplified/countries/af.svg" height="20"> | [✓](full-size/countries/af.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://en.wikipedia.org/wiki/File:Flag_of_Afghanistan_(2013–2021).svg)<br>[<img src="swatches/D32011.svg" width="12">`#D32011`](https://en.wikipedia.org/wiki/File:Flag_of_Afghanistan_(2013–2021).svg)<br>[<img src="swatches/007A36.svg" width="12">`#007A36`](https://en.wikipedia.org/wiki/File:Flag_of_Afghanistan_(2013–2021).svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Afghanistan_(2013–2021).svg) |
| `al` | [Albania](https://en.wikipedia.org/wiki/Albania) | <img src="circle/countries/al.svg" width="32"> | <img src="square/countries/al.svg" width="32"> | <img src="full-size-simplified/countries/al.svg" height="20"> | [✓](full-size/countries/al.svg) | [<img src="swatches/E41E20.svg" width="12">`#E41E20`](https://en.wikipedia.org/wiki/File:Flag_of_Albania.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://en.wikipedia.org/wiki/File:Flag_of_Albania.svg) |
| `dz` | [Algeria](https://en.wikipedia.org/wiki/Algeria) | <img src="circle/countries/dz.svg" width="32"> | <img src="square/countries/dz.svg" width="32"> | <img src="full-size-simplified/countries/dz.svg" height="20"> | [✓](full-size/countries/dz.svg) | [<img src="swatches/006633.svg" width="12">`#006633`](https://commons.wikimedia.org/wiki/File:Flag_of_Algeria.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Algeria.svg)<br>[<img src="swatches/D21034.svg" width="12">`#D21034`](https://commons.wikimedia.org/wiki/File:Flag_of_Algeria.svg) |
| `ad` | [Andorra](https://en.wikipedia.org/wiki/Andorra) | | | | | |
| `ao` | [Angola](https://en.wikipedia.org/wiki/Angola) | | | | | |
| `ag` | [Antigua and Barbuda](https://en.wikipedia.org/wiki/Antigua_and_Barbuda) | | | | | |
| `ar` | [Argentina](https://en.wikipedia.org/wiki/Argentina) | <img src="circle/countries/ar.svg" width="32"> | <img src="square/countries/ar.svg" width="32"> | <img src="full-size-simplified/countries/ar.svg" height="20"> | [✓](full-size/countries/ar.svg) | [<img src="swatches/74ACDF.svg" width="12">`#74ACDF`](https://commons.wikimedia.org/wiki/File:Flag_of_Argentina.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Argentina.svg)<br>[<img src="swatches/F6B40E.svg" width="12">`#F6B40E`](https://commons.wikimedia.org/wiki/File:Flag_of_Argentina.svg)<br>[<img src="swatches/85340A.svg" width="12">`#85340A`](https://commons.wikimedia.org/wiki/File:Flag_of_Argentina.svg) |
| `am` | [Armenia](https://en.wikipedia.org/wiki/Armenia) | | | | | |
| `au` | [Australia](https://en.wikipedia.org/wiki/Australia) | <img src="circle/countries/au.svg" width="32"> | <img src="square/countries/au.svg" width="32"> | <img src="full-size-simplified/countries/au.svg" height="20"> | [✓](full-size/countries/au.svg) | [<img src="swatches/012169.svg" width="12">`#012169`](https://commons.wikimedia.org/wiki/File:Flag_of_Australia_(converted).svg)<br>[<img src="swatches/E4002B.svg" width="12">`#E4002B`](https://commons.wikimedia.org/wiki/File:Flag_of_Australia_(converted).svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Australia_(converted).svg) |
| `at` | [Austria](https://en.wikipedia.org/wiki/Austria) | | | | | |
| `az` | [Azerbaijan](https://en.wikipedia.org/wiki/Azerbaijan) | <img src="circle/countries/az.svg" width="32"> | <img src="square/countries/az.svg" width="32"> | <img src="full-size-simplified/countries/az.svg" height="20"> | [✓](full-size/countries/az.svg) | [<img src="swatches/00B5E2.svg" width="12">`#00B5E2`](https://commons.wikimedia.org/wiki/File:Flag_of_Azerbaijan.svg)<br>[<img src="swatches/EF3340.svg" width="12">`#EF3340`](https://commons.wikimedia.org/wiki/File:Flag_of_Azerbaijan.svg)<br>[<img src="swatches/509E2F.svg" width="12">`#509E2F`](https://commons.wikimedia.org/wiki/File:Flag_of_Azerbaijan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Azerbaijan.svg) |
| `bs` | [Bahamas](https://en.wikipedia.org/wiki/The_Bahamas) | <img src="circle/countries/bs.svg" width="32"> | <img src="square/countries/bs.svg" width="32"> | <img src="full-size-simplified/countries/bs.svg" height="20"> | [✓](full-size/countries/bs.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Bahamas.svg)<br>[<img src="swatches/00778B.svg" width="12">`#00778B`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Bahamas.svg)<br>[<img src="swatches/FFC72C.svg" width="12">`#FFC72C`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Bahamas.svg) |
| `bh` | [Bahrain](https://en.wikipedia.org/wiki/Bahrain) | | | | | |
| `bd` | [Bangladesh](https://en.wikipedia.org/wiki/Bangladesh) | <img src="circle/countries/bd.svg" width="32"> | <img src="square/countries/bd.svg" width="32"> | <img src="full-size-simplified/countries/bd.svg" height="20"> | [✓](full-size/countries/bd.svg) | [<img src="swatches/006747.svg" width="12">`#006747`](https://commons.wikimedia.org/wiki/File:Flag_of_Bangladesh.svg)<br>[<img src="swatches/DA291C.svg" width="12">`#DA291C`](https://commons.wikimedia.org/wiki/File:Flag_of_Bangladesh.svg) |
| `bb` | [Barbados](https://en.wikipedia.org/wiki/Barbados) | <img src="circle/countries/bb.svg" width="32"> | <img src="square/countries/bb.svg" width="32"> | <img src="full-size-simplified/countries/bb.svg" height="20"> | [✓](full-size/countries/bb.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Barbados.svg)<br>[<img src="swatches/00267F.svg" width="12">`#00267F`](https://commons.wikimedia.org/wiki/File:Flag_of_Barbados.svg)<br>[<img src="swatches/FFC726.svg" width="12">`#FFC726`](https://commons.wikimedia.org/wiki/File:Flag_of_Barbados.svg) |
| `by` | [Belarus](https://en.wikipedia.org/wiki/Belarus) | <img src="circle/countries/by.svg" width="32"> | <img src="square/countries/by.svg" width="32"> | <img src="full-size-simplified/countries/by.svg" height="20"> | [✓](full-size/countries/by.svg) | [<img src="swatches/007C30.svg" width="12">`#007C30`](https://commons.wikimedia.org/wiki/File:Flag_of_Belarus.svg)<br>[<img src="swatches/CE1720.svg" width="12">`#CE1720`](https://commons.wikimedia.org/wiki/File:Flag_of_Belarus.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Belarus.svg) |
| `be` | [Belgium](https://en.wikipedia.org/wiki/Belgium) | <img src="circle/countries/be.svg" width="32"> | <img src="square/countries/be.svg" width="32"> | <img src="full-size-simplified/countries/be.svg" height="20"> | [✓](full-size/countries/be.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Belgium.svg)<br>[<img src="swatches/EF3340.svg" width="12">`#EF3340`](https://commons.wikimedia.org/wiki/File:Flag_of_Belgium.svg)<br>[<img src="swatches/FDDA25.svg" width="12">`#FDDA25`](https://commons.wikimedia.org/wiki/File:Flag_of_Belgium.svg) |
| `bz` | [Belize](https://en.wikipedia.org/wiki/Belize) | <img src="circle/countries/bz.svg" width="32"> | <img src="square/countries/bz.svg" width="32"> | <img src="full-size-simplified/countries/bz.svg" height="20"> | [✓](full-size/countries/bz.svg) | [<img src="swatches/006AC8.svg" width="12">`#006AC8`](https://commons.wikimedia.org/wiki/File:Flag_of_Belize.svg)<br>[<img src="swatches/AD7D5A.svg" width="12">`#AD7D5A`](https://commons.wikimedia.org/wiki/File:Flag_of_Belize.svg)<br>[<img src="swatches/D90F19.svg" width="12">`#D90F19`](https://commons.wikimedia.org/wiki/File:Flag_of_Belize.svg)<br>[<img src="swatches/FFE682.svg" width="12">`#FFE682`](https://commons.wikimedia.org/wiki/File:Flag_of_Belize.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Belize.svg) |
| `bj` | [Benin](https://en.wikipedia.org/wiki/Benin) | <img src="circle/countries/bj.svg" width="32"> | <img src="square/countries/bj.svg" width="32"> | <img src="full-size-simplified/countries/bj.svg" height="20"> | [✓](full-size/countries/bj.svg) | [<img src="swatches/008751.svg" width="12">`#008751`](https://commons.wikimedia.org/wiki/File:Flag_of_Benin.svg)<br>[<img src="swatches/E8112D.svg" width="12">`#E8112D`](https://commons.wikimedia.org/wiki/File:Flag_of_Benin.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Benin.svg) |
| `bt` | [Bhutan](https://en.wikipedia.org/wiki/Bhutan) | | | | | |
| `bo` | [Bolivia](https://en.wikipedia.org/wiki/Bolivia) | | | | | |
| `ba` | [Bosnia and Herzegovina](https://en.wikipedia.org/wiki/Bosnia_and_Herzegovina) | <img src="circle/countries/ba.svg" width="32"> | <img src="square/countries/ba.svg" width="32"> | <img src="full-size-simplified/countries/ba.svg" height="20"> | [✓](full-size/countries/ba.svg) | [<img src="swatches/002395.svg" width="12">`#002395`](https://en.wikipedia.org/wiki/File:Flag_of_Bosnia_and_Herzegovina.svg)<br>[<img src="swatches/FECB00.svg" width="12">`#FECB00`](https://en.wikipedia.org/wiki/File:Flag_of_Bosnia_and_Herzegovina.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Bosnia_and_Herzegovina.svg) |
| `bw` | [Botswana](https://en.wikipedia.org/wiki/Botswana) | <img src="circle/countries/bw.svg" width="32"> | <img src="square/countries/bw.svg" width="32"> | <img src="full-size-simplified/countries/bw.svg" height="20"> | [✓](full-size/countries/bw.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Botswana.svg)<br>[<img src="swatches/6DA9D2.svg" width="12">`#6DA9D2`](https://commons.wikimedia.org/wiki/File:Flag_of_Botswana.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Botswana.svg) |
| `br` | [Brazil](https://en.wikipedia.org/wiki/Brazil) | <img src="circle/countries/br.svg" width="32"> | <img src="square/countries/br.svg" width="32"> | <img src="full-size-simplified/countries/br.svg" height="20"> | [✓](full-size/countries/br.svg) | [<img src="swatches/009440.svg" width="12">`#009440`](https://commons.wikimedia.org/wiki/File:Flag_of_Brazil.svg)<br>[<img src="swatches/FFCB00.svg" width="12">`#FFCB00`](https://commons.wikimedia.org/wiki/File:Flag_of_Brazil.svg)<br>[<img src="swatches/302681.svg" width="12">`#302681`](https://commons.wikimedia.org/wiki/File:Flag_of_Brazil.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Brazil.svg) |
| `bn` | [Brunei](https://en.wikipedia.org/wiki/Brunei) | | | | | |
| `bg` | [Bulgaria](https://en.wikipedia.org/wiki/Bulgaria) | | | | | |
| `bf` | [Burkina Faso](https://en.wikipedia.org/wiki/Burkina_Faso) | <img src="circle/countries/bf.svg" width="32"> | <img src="square/countries/bf.svg" width="32"> | <img src="full-size-simplified/countries/bf.svg" height="20"> | [✓](full-size/countries/bf.svg) | [<img src="swatches/009E49.svg" width="12">`#009E49`](https://commons.wikimedia.org/wiki/File:Flag_of_Burkina_Faso.svg)<br>[<img src="swatches/EF2B2D.svg" width="12">`#EF2B2D`](https://commons.wikimedia.org/wiki/File:Flag_of_Burkina_Faso.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Burkina_Faso.svg) |
| `bi` | [Burundi](https://en.wikipedia.org/wiki/Burundi) | <img src="circle/countries/bi.svg" width="32"> | <img src="square/countries/bi.svg" width="32"> | <img src="full-size-simplified/countries/bi.svg" height="20"> | [✓](full-size/countries/bi.svg) | [<img src="swatches/43B02A.svg" width="12">`#43B02A`](https://commons.wikimedia.org/wiki/File:Flag_of_Burundi.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Burundi.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Burundi.svg) |
| `cv` | [Cabo Verde](https://en.wikipedia.org/wiki/Cape_Verde) | | | | | |
| `kh` | [Cambodia](https://en.wikipedia.org/wiki/Cambodia) | <img src="circle/countries/kh.svg" width="32"> | <img src="square/countries/kh.svg" width="32"> | <img src="full-size-simplified/countries/kh.svg" height="20"> | [✓](full-size/countries/kh.svg) | [<img src="swatches/032EA1.svg" width="12">`#032EA1`](https://commons.wikimedia.org/wiki/File:Flag_of_Cambodia.svg)<br>[<img src="swatches/E00025.svg" width="12">`#E00025`](https://commons.wikimedia.org/wiki/File:Flag_of_Cambodia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Cambodia.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Cambodia.svg) |
| `cm` | [Cameroon](https://en.wikipedia.org/wiki/Cameroon) | <img src="circle/countries/cm.svg" width="32"> | <img src="square/countries/cm.svg" width="32"> | <img src="full-size-simplified/countries/cm.svg" height="20"> | [✓](full-size/countries/cm.svg) | [<img src="swatches/007A5E.svg" width="12">`#007A5E`](https://commons.wikimedia.org/wiki/File:Flag_of_Cameroon.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Cameroon.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Cameroon.svg) |
| `ca` | [Canada](https://en.wikipedia.org/wiki/Canada) | <img src="circle/countries/ca.svg" width="32"> | <img src="square/countries/ca.svg" width="32"> | <img src="full-size-simplified/countries/ca.svg" height="20"> | [✓](full-size/countries/ca.svg) | [<img src="swatches/D52B1E.svg" width="12">`#D52B1E`](https://commons.wikimedia.org/wiki/File:Flag_of_Canada_(Pantone).svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Canada_(Pantone).svg) |
| `cf` | [Central African Republic](https://en.wikipedia.org/wiki/Central_African_Republic) | <img src="circle/countries/cf.svg" width="32"> | <img src="square/countries/cf.svg" width="32"> | <img src="full-size-simplified/countries/cf.svg" height="20"> | [✓](full-size/countries/cf.svg) | [<img src="swatches/003082.svg" width="12">`#003082`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Central_African_Republic.svg)<br>[<img src="swatches/289728.svg" width="12">`#289728`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Central_African_Republic.svg)<br>[<img src="swatches/D21034.svg" width="12">`#D21034`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Central_African_Republic.svg)<br>[<img src="swatches/FFCE00.svg" width="12">`#FFCE00`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Central_African_Republic.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Central_African_Republic.svg) |
| `td` | [Chad](https://en.wikipedia.org/wiki/Chad) | <img src="circle/countries/td.svg" width="32"> | <img src="square/countries/td.svg" width="32"> | <img src="full-size-simplified/countries/td.svg" height="20"> | [✓](full-size/countries/td.svg) | [<img src="swatches/002664.svg" width="12">`#002664`](https://commons.wikimedia.org/wiki/File:Flag_of_Chad.svg)<br>[<img src="swatches/C60C30.svg" width="12">`#C60C30`](https://commons.wikimedia.org/wiki/File:Flag_of_Chad.svg)<br>[<img src="swatches/FECB00.svg" width="12">`#FECB00`](https://commons.wikimedia.org/wiki/File:Flag_of_Chad.svg) |
| `cl` | [Chile](https://en.wikipedia.org/wiki/Chile) | <img src="circle/countries/cl.svg" width="32"> | <img src="square/countries/cl.svg" width="32"> | <img src="full-size-simplified/countries/cl.svg" height="20"> | [✓](full-size/countries/cl.svg) | [<img src="swatches/0032A0.svg" width="12">`#0032A0`](https://commons.wikimedia.org/wiki/File:Flag_of_Chile.svg)<br>[<img src="swatches/DA291C.svg" width="12">`#DA291C`](https://commons.wikimedia.org/wiki/File:Flag_of_Chile.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Chile.svg) |
| `cn` | [China](https://en.wikipedia.org/wiki/China) | <img src="circle/countries/cn.svg" width="32"> | <img src="square/countries/cn.svg" width="32"> | <img src="full-size-simplified/countries/cn.svg" height="20"> | [✓](full-size/countries/cn.svg) | [<img src="swatches/EE1C25.svg" width="12">`#EE1C25`](https://commons.wikimedia.org/wiki/File:Flag_of_the_People%27s_Republic_of_China.svg)<br>[<img src="swatches/FFFF00.svg" width="12">`#FFFF00`](https://commons.wikimedia.org/wiki/File:Flag_of_the_People%27s_Republic_of_China.svg) |
| `co` | [Colombia](https://en.wikipedia.org/wiki/Colombia) | <img src="circle/countries/co.svg" width="32"> | <img src="square/countries/co.svg" width="32"> | <img src="full-size-simplified/countries/co.svg" height="20"> | [✓](full-size/countries/co.svg) | [<img src="swatches/003087.svg" width="12">`#003087`](https://commons.wikimedia.org/wiki/File:Flag_of_Colombia.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Colombia.svg)<br>[<img src="swatches/FFCD00.svg" width="12">`#FFCD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Colombia.svg) |
| `km` | [Comoros](https://en.wikipedia.org/wiki/Comoros) | <img src="circle/countries/km.svg" width="32"> | <img src="square/countries/km.svg" width="32"> | <img src="full-size-simplified/countries/km.svg" height="20"> | [✓](full-size/countries/km.svg) | [<img src="swatches/003DA5.svg" width="12">`#003DA5`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Comoros.svg)<br>[<img src="swatches/009639.svg" width="12">`#009639`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Comoros.svg)<br>[<img src="swatches/EF3340.svg" width="12">`#EF3340`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Comoros.svg)<br>[<img src="swatches/FFD100.svg" width="12">`#FFD100`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Comoros.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Comoros.svg) |
| `cg` | [Congo](https://en.wikipedia.org/wiki/Republic_of_the_Congo) | <img src="circle/countries/cg.svg" width="32"> | <img src="square/countries/cg.svg" width="32"> | <img src="full-size-simplified/countries/cg.svg" height="20"> | [✓](full-size/countries/cg.svg) | [<img src="swatches/009739.svg" width="12">`#009739`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_the_Congo.svg)<br>[<img src="swatches/DC241F.svg" width="12">`#DC241F`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_the_Congo.svg)<br>[<img src="swatches/FFD100.svg" width="12">`#FFD100`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_the_Congo.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_the_Congo.svg) |
| `cd` | [Congo (DRC)](https://en.wikipedia.org/wiki/Democratic_Republic_of_the_Congo) | <img src="circle/countries/cd.svg" width="32"> | <img src="square/countries/cd.svg" width="32"> | <img src="full-size-simplified/countries/cd.svg" height="20"> | [✓](full-size/countries/cd.svg) | [<img src="swatches/007FFF.svg" width="12">`#007FFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Democratic_Republic_of_the_Congo.svg)<br>[<img src="swatches/CE1021.svg" width="12">`#CE1021`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Democratic_Republic_of_the_Congo.svg)<br>[<img src="swatches/F7D618.svg" width="12">`#F7D618`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Democratic_Republic_of_the_Congo.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Democratic_Republic_of_the_Congo.svg) |
| `cr` | [Costa Rica](https://en.wikipedia.org/wiki/Costa_Rica) | | | | | |
| `hr` | [Croatia](https://en.wikipedia.org/wiki/Croatia) | <img src="circle/countries/hr.svg" width="32"> | <img src="square/countries/hr.svg" width="32"> | <img src="full-size-simplified/countries/hr.svg" height="20"> | [✓](full-size/countries/hr.svg) | [<img src="swatches/FF0000.svg" width="12">`#FF0000`](https://commons.wikimedia.org/wiki/File:Flag_of_Croatia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Croatia.svg)<br>[<img src="swatches/171796.svg" width="12">`#171796`](https://commons.wikimedia.org/wiki/File:Flag_of_Croatia.svg)<br>[<img src="swatches/0093DD.svg" width="12">`#0093DD`](https://commons.wikimedia.org/wiki/File:Flag_of_Croatia.svg)<br>[<img src="swatches/F7DB17.svg" width="12">`#F7DB17`](https://commons.wikimedia.org/wiki/File:Flag_of_Croatia.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Croatia.svg) |
| `cu` | [Cuba](https://en.wikipedia.org/wiki/Cuba) | | | | | |
| `cy` | [Cyprus](https://en.wikipedia.org/wiki/Cyprus) | | | | | |
| `cz` | [Czechia](https://en.wikipedia.org/wiki/Czech_Republic) | <img src="circle/countries/cz.svg" width="32"> | <img src="square/countries/cz.svg" width="32"> | <img src="full-size-simplified/countries/cz.svg" height="20"> | [✓](full-size/countries/cz.svg) | [<img src="swatches/11457E.svg" width="12">`#11457E`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Czech_Republic.svg)<br>[<img src="swatches/D7141A.svg" width="12">`#D7141A`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Czech_Republic.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Czech_Republic.svg) |
| `ci` | [Côte d'Ivoire](https://en.wikipedia.org/wiki/Ivory_Coast) | <img src="circle/countries/ci.svg" width="32"> | <img src="square/countries/ci.svg" width="32"> | <img src="full-size-simplified/countries/ci.svg" height="20"> | [✓](full-size/countries/ci.svg) | [<img src="swatches/009A44.svg" width="12">`#009A44`](https://commons.wikimedia.org/wiki/File:Flag_of_Côte_d'Ivoire.svg)<br>[<img src="swatches/FF8200.svg" width="12">`#FF8200`](https://commons.wikimedia.org/wiki/File:Flag_of_Côte_d'Ivoire.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Côte_d'Ivoire.svg) |
| `dk` | [Denmark](https://en.wikipedia.org/wiki/Denmark) | <img src="circle/countries/dk.svg" width="32"> | <img src="square/countries/dk.svg" width="32"> | <img src="full-size-simplified/countries/dk.svg" height="20"> | [✓](full-size/countries/dk.svg) | [<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://en.wikipedia.org/wiki/File:Flag_of_Denmark.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Denmark.svg) |
| `dj` | [Djibouti](https://en.wikipedia.org/wiki/Djibouti) | <img src="circle/countries/dj.svg" width="32"> | <img src="square/countries/dj.svg" width="32"> | <img src="full-size-simplified/countries/dj.svg" height="20"> | [✓](full-size/countries/dj.svg) | [<img src="swatches/12AD2B.svg" width="12">`#12AD2B`](https://commons.wikimedia.org/wiki/File:Flag_of_Djibouti.svg)<br>[<img src="swatches/6AB2E7.svg" width="12">`#6AB2E7`](https://commons.wikimedia.org/wiki/File:Flag_of_Djibouti.svg)<br>[<img src="swatches/D7141A.svg" width="12">`#D7141A`](https://commons.wikimedia.org/wiki/File:Flag_of_Djibouti.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Djibouti.svg) |
| `dm` | [Dominica](https://en.wikipedia.org/wiki/Dominica) | <img src="circle/countries/dm.svg" width="32"> | <img src="square/countries/dm.svg" width="32"> | <img src="full-size-simplified/countries/dm.svg" height="20"> | [✓](full-size/countries/dm.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Dominica.svg)<br>[<img src="swatches/046A38.svg" width="12">`#046A38`](https://commons.wikimedia.org/wiki/File:Flag_of_Dominica.svg)<br>[<img src="swatches/D50032.svg" width="12">`#D50032`](https://commons.wikimedia.org/wiki/File:Flag_of_Dominica.svg)<br>[<img src="swatches/FFCD00.svg" width="12">`#FFCD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Dominica.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Dominica.svg) |
| `do` | [Dominican Republic](https://en.wikipedia.org/wiki/Dominican_Republic) | | | | | |
| `ec` | [Ecuador](https://en.wikipedia.org/wiki/Ecuador) | | | | | |
| `eg` | [Egypt](https://en.wikipedia.org/wiki/Egypt) | <img src="circle/countries/eg.svg" width="32"> | <img src="square/countries/eg.svg" width="32"> | <img src="full-size-simplified/countries/eg.svg" height="20"> | [✓](full-size/countries/eg.svg) | [<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Egypt.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Egypt.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Egypt.svg)<br>[<img src="swatches/FFCD00.svg" width="12">`#FFCD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Egypt.svg) |
| `sv` | [El Salvador](https://en.wikipedia.org/wiki/El_Salvador) | | | | | |
| `gq` | [Equatorial Guinea](https://en.wikipedia.org/wiki/Equatorial_Guinea) | <img src="circle/countries/gq.svg" width="32"> | <img src="square/countries/gq.svg" width="32"> | <img src="full-size-simplified/countries/gq.svg" height="20"> | [✓](full-size/countries/gq.svg) | [<img src="swatches/0073CE.svg" width="12">`#0073CE`](https://commons.wikimedia.org/wiki/File:Flag_of_Equatorial_Guinea.svg)<br>[<img src="swatches/3E9A00.svg" width="12">`#3E9A00`](https://commons.wikimedia.org/wiki/File:Flag_of_Equatorial_Guinea.svg)<br>[<img src="swatches/A36629.svg" width="12">`#A36629`](https://commons.wikimedia.org/wiki/File:Flag_of_Equatorial_Guinea.svg)<br>[<img src="swatches/DDDDDD.svg" width="12">`#DDDDDD`](https://commons.wikimedia.org/wiki/File:Flag_of_Equatorial_Guinea.svg)<br>[<img src="swatches/E32118.svg" width="12">`#E32118`](https://commons.wikimedia.org/wiki/File:Flag_of_Equatorial_Guinea.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Equatorial_Guinea.svg) |
| `er` | [Eritrea](https://en.wikipedia.org/wiki/Eritrea) | | | | | |
| `ee` | [Estonia](https://en.wikipedia.org/wiki/Estonia) | <img src="circle/countries/ee.svg" width="32"> | <img src="square/countries/ee.svg" width="32"> | <img src="full-size-simplified/countries/ee.svg" height="20"> | [✓](full-size/countries/ee.svg) | [<img src="swatches/0072CE.svg" width="12">`#0072CE`](https://commons.wikimedia.org/wiki/File:Flag_of_Estonia.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Estonia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Estonia.svg) |
| `sz` | [Eswatini](https://en.wikipedia.org/wiki/Eswatini) | | | | | |
| `et` | [Ethiopia](https://en.wikipedia.org/wiki/Ethiopia) | <img src="circle/countries/et.svg" width="32"> | <img src="square/countries/et.svg" width="32"> | <img src="full-size-simplified/countries/et.svg" height="20"> | [✓](full-size/countries/et.svg) | [<img src="swatches/078930.svg" width="12">`#078930`](https://commons.wikimedia.org/wiki/File:Flag_of_Ethiopia.svg)<br>[<img src="swatches/0F47AF.svg" width="12">`#0F47AF`](https://commons.wikimedia.org/wiki/File:Flag_of_Ethiopia.svg)<br>[<img src="swatches/DA121A.svg" width="12">`#DA121A`](https://commons.wikimedia.org/wiki/File:Flag_of_Ethiopia.svg)<br>[<img src="swatches/FCDD09.svg" width="12">`#FCDD09`](https://commons.wikimedia.org/wiki/File:Flag_of_Ethiopia.svg) |
| `fj` | [Fiji](https://en.wikipedia.org/wiki/Fiji) | <img src="circle/countries/fj.svg" width="32"> | <img src="square/countries/fj.svg" width="32"> | <img src="full-size-simplified/countries/fj.svg" height="20"> | [✓](full-size/countries/fj.svg) | [<img src="swatches/012169.svg" width="12">`#012169`](https://commons.wikimedia.org/wiki/File:Flag_of_Fiji.svg)<br>[<img src="swatches/62B5E5.svg" width="12">`#62B5E5`](https://commons.wikimedia.org/wiki/File:Flag_of_Fiji.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Fiji.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Fiji.svg) |
| `fi` | [Finland](https://en.wikipedia.org/wiki/Finland) | <img src="circle/countries/fi.svg" width="32"> | <img src="square/countries/fi.svg" width="32"> | <img src="full-size-simplified/countries/fi.svg" height="20"> | [✓](full-size/countries/fi.svg) | [<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Finland.svg)<br>[<img src="swatches/002F6C.svg" width="12">`#002F6C`](https://en.wikipedia.org/wiki/File:Flag_of_Finland.svg) |
| `ga` | [Gabon](https://en.wikipedia.org/wiki/Gabon) | <img src="circle/countries/ga.svg" width="32"> | <img src="square/countries/ga.svg" width="32"> | <img src="full-size-simplified/countries/ga.svg" height="20"> | [✓](full-size/countries/ga.svg) | [<img src="swatches/009E60.svg" width="12">`#009E60`](https://commons.wikimedia.org/wiki/File:Flag_of_Gabon.svg)<br>[<img src="swatches/3A75C4.svg" width="12">`#3A75C4`](https://commons.wikimedia.org/wiki/File:Flag_of_Gabon.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Gabon.svg) |
| `gm` | [Gambia](https://en.wikipedia.org/wiki/The_Gambia) | <img src="circle/countries/gm.svg" width="32"> | <img src="square/countries/gm.svg" width="32"> | <img src="full-size-simplified/countries/gm.svg" height="20"> | [✓](full-size/countries/gm.svg) | [<img src="swatches/0C1C8C.svg" width="12">`#0C1C8C`](https://commons.wikimedia.org/wiki/File:Flag_of_The_Gambia.svg)<br>[<img src="swatches/3A7728.svg" width="12">`#3A7728`](https://commons.wikimedia.org/wiki/File:Flag_of_The_Gambia.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_The_Gambia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_The_Gambia.svg) |
| `ge` | [Georgia](https://en.wikipedia.org/wiki/Georgia_(country)) | <img src="circle/countries/ge.svg" width="32"> | <img src="square/countries/ge.svg" width="32"> | <img src="full-size-simplified/countries/ge.svg" height="20"> | [✓](full-size/countries/ge.svg) | [<img src="swatches/FF0000.svg" width="12">`#FF0000`](https://commons.wikimedia.org/wiki/File:Flag_of_Georgia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Georgia.svg) |
| `gh` | [Ghana](https://en.wikipedia.org/wiki/Ghana) | <img src="circle/countries/gh.svg" width="32"> | <img src="square/countries/gh.svg" width="32"> | <img src="full-size-simplified/countries/gh.svg" height="20"> | [✓](full-size/countries/gh.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Ghana.svg)<br>[<img src="swatches/006B3F.svg" width="12">`#006B3F`](https://commons.wikimedia.org/wiki/File:Flag_of_Ghana.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Ghana.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Ghana.svg) |
| `gd` | [Grenada](https://en.wikipedia.org/wiki/Grenada) | <img src="circle/countries/gd.svg" width="32"> | <img src="square/countries/gd.svg" width="32"> | <img src="full-size-simplified/countries/gd.svg" height="20"> | [✓](full-size/countries/gd.svg) | [<img src="swatches/007A5E.svg" width="12">`#007A5E`](https://commons.wikimedia.org/wiki/File:Flag_of_Grenada.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Grenada.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Grenada.svg) |
| `gt` | [Guatemala](https://en.wikipedia.org/wiki/Guatemala) | | | | | |
| `gn` | [Guinea](https://en.wikipedia.org/wiki/Guinea) | <img src="circle/countries/gn.svg" width="32"> | <img src="square/countries/gn.svg" width="32"> | <img src="full-size-simplified/countries/gn.svg" height="20"> | [✓](full-size/countries/gn.svg) | [<img src="swatches/009460.svg" width="12">`#009460`](https://commons.wikimedia.org/wiki/File:Flag_of_Guinea.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Guinea.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Guinea.svg) |
| `gw` | [Guinea-Bissau](https://en.wikipedia.org/wiki/Guinea-Bissau) | | | | | |
| `gy` | [Guyana](https://en.wikipedia.org/wiki/Guyana) | <img src="circle/countries/gy.svg" width="32"> | <img src="square/countries/gy.svg" width="32"> | <img src="full-size-simplified/countries/gy.svg" height="20"> | [✓](full-size/countries/gy.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Guyana.svg)<br>[<img src="swatches/2A936A.svg" width="12">`#2A936A`](https://commons.wikimedia.org/wiki/File:Flag_of_Guyana.svg)<br>[<img src="swatches/BE1E2D.svg" width="12">`#BE1E2D`](https://commons.wikimedia.org/wiki/File:Flag_of_Guyana.svg)<br>[<img src="swatches/FFC20E.svg" width="12">`#FFC20E`](https://commons.wikimedia.org/wiki/File:Flag_of_Guyana.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Guyana.svg) |
| `ht` | [Haiti](https://en.wikipedia.org/wiki/Haiti) | <img src="circle/countries/ht.svg" width="32"> | <img src="square/countries/ht.svg" width="32"> | <img src="full-size-simplified/countries/ht.svg" height="20"> | [✓](full-size/countries/ht.svg) | [<img src="swatches/00209F.svg" width="12">`#00209F`](https://commons.wikimedia.org/wiki/File:Flag_of_Haiti.svg)<br>[<img src="swatches/016A16.svg" width="12">`#016A16`](https://commons.wikimedia.org/wiki/File:Flag_of_Haiti.svg)<br>[<img src="swatches/D21034.svg" width="12">`#D21034`](https://commons.wikimedia.org/wiki/File:Flag_of_Haiti.svg)<br>[<img src="swatches/F1B617.svg" width="12">`#F1B617`](https://commons.wikimedia.org/wiki/File:Flag_of_Haiti.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Haiti.svg) |
| `hn` | [Honduras](https://en.wikipedia.org/wiki/Honduras) | | | | | |
| `hu` | [Hungary](https://en.wikipedia.org/wiki/Hungary) | <img src="circle/countries/hu.svg" width="32"> | <img src="square/countries/hu.svg" width="32"> | <img src="full-size-simplified/countries/hu.svg" height="20"> | [✓](full-size/countries/hu.svg) | [<img src="swatches/CE2939.svg" width="12">`#CE2939`](https://en.wikipedia.org/wiki/File:Flag_of_Hungary.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Hungary.svg)<br>[<img src="swatches/477050.svg" width="12">`#477050`](https://en.wikipedia.org/wiki/File:Flag_of_Hungary.svg) |
| `is` | [Iceland](https://en.wikipedia.org/wiki/Iceland) | <img src="circle/countries/is.svg" width="32"> | <img src="square/countries/is.svg" width="32"> | <img src="full-size-simplified/countries/is.svg" height="20"> | [✓](full-size/countries/is.svg) | [<img src="swatches/02529C.svg" width="12">`#02529C`](https://commons.wikimedia.org/wiki/File:Flag_of_Iceland.svg)<br>[<img src="swatches/DC1E35.svg" width="12">`#DC1E35`](https://commons.wikimedia.org/wiki/File:Flag_of_Iceland.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Iceland.svg) |
| `in` | [India](https://en.wikipedia.org/wiki/India) | <img src="circle/countries/in.svg" width="32"> | <img src="square/countries/in.svg" width="32"> | <img src="full-size-simplified/countries/in.svg" height="20"> | [✓](full-size/countries/in.svg) | [<img src="swatches/046A38.svg" width="12">`#046A38`](https://commons.wikimedia.org/wiki/File:Flag_of_India.svg)<br>[<img src="swatches/07038D.svg" width="12">`#07038D`](https://commons.wikimedia.org/wiki/File:Flag_of_India.svg)<br>[<img src="swatches/FF6820.svg" width="12">`#FF6820`](https://commons.wikimedia.org/wiki/File:Flag_of_India.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_India.svg) |
| `id` | [Indonesia](https://en.wikipedia.org/wiki/Indonesia) | <img src="circle/countries/id.svg" width="32"> | <img src="square/countries/id.svg" width="32"> | <img src="full-size-simplified/countries/id.svg" height="20"> | [✓](full-size/countries/id.svg) | [<img src="swatches/FF0000.svg" width="12">`#FF0000`](https://commons.wikimedia.org/wiki/File:Flag_of_Indonesia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Indonesia.svg) |
| `ir` | [Iran](https://en.wikipedia.org/wiki/Iran) | <img src="circle/countries/ir.svg" width="32"> | <img src="square/countries/ir.svg" width="32"> | <img src="full-size-simplified/countries/ir.svg" height="20"> | [✓](full-size/countries/ir.svg) | [<img src="swatches/239F40.svg" width="12">`#239F40`](https://en.wikipedia.org/wiki/File:Flag_of_Iran.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Iran.svg)<br>[<img src="swatches/DA0000.svg" width="12">`#DA0000`](https://en.wikipedia.org/wiki/File:Flag_of_Iran.svg) |
| `iq` | [Iraq](https://en.wikipedia.org/wiki/Iraq) | <img src="circle/countries/iq.svg" width="32"> | <img src="square/countries/iq.svg" width="32"> | <img src="full-size-simplified/countries/iq.svg" height="20"> | [✓](full-size/countries/iq.svg) | [<img src="swatches/CD1125.svg" width="12">`#CD1125`](https://commons.wikimedia.org/wiki/File:Flag_of_Iraq.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Iraq.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Iraq.svg)<br>[<img src="swatches/017B3D.svg" width="12">`#017B3D`](https://commons.wikimedia.org/wiki/File:Flag_of_Iraq.svg) |
| `ie` | [Ireland](https://en.wikipedia.org/wiki/Republic_of_Ireland) | <img src="circle/countries/ie.svg" width="32"> | <img src="square/countries/ie.svg" width="32"> | <img src="full-size-simplified/countries/ie.svg" height="20"> | [✓](full-size/countries/ie.svg) | [<img src="swatches/169B62.svg" width="12">`#169B62`](https://commons.wikimedia.org/wiki/File:Flag_of_Ireland.svg)<br>[<img src="swatches/FF883E.svg" width="12">`#FF883E`](https://commons.wikimedia.org/wiki/File:Flag_of_Ireland.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Ireland.svg) |
| `il` | [Israel](https://en.wikipedia.org/wiki/Israel) | <img src="circle/countries/il.svg" width="32"> | <img src="square/countries/il.svg" width="32"> | <img src="full-size-simplified/countries/il.svg" height="20"> | [✓](full-size/countries/il.svg) | [<img src="swatches/0038B8.svg" width="12">`#0038B8`](https://en.wikipedia.org/wiki/File:Flag_of_Israel.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Israel.svg) |
| `it` | [Italy](https://en.wikipedia.org/wiki/Italy) | <img src="circle/countries/it.svg" width="32"> | <img src="square/countries/it.svg" width="32"> | <img src="full-size-simplified/countries/it.svg" height="20"> | [✓](full-size/countries/it.svg) | [<img src="swatches/009246.svg" width="12">`#009246`](https://en.wikipedia.org/wiki/File:Flag_of_Italy.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Italy.svg)<br>[<img src="swatches/CE2B37.svg" width="12">`#CE2B37`](https://en.wikipedia.org/wiki/File:Flag_of_Italy.svg) |
| `jm` | [Jamaica](https://en.wikipedia.org/wiki/Jamaica) | <img src="circle/countries/jm.svg" width="32"> | <img src="square/countries/jm.svg" width="32"> | <img src="full-size-simplified/countries/jm.svg" height="20"> | [✓](full-size/countries/jm.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Jamaica.svg)<br>[<img src="swatches/007749.svg" width="12">`#007749`](https://commons.wikimedia.org/wiki/File:Flag_of_Jamaica.svg)<br>[<img src="swatches/FFB81C.svg" width="12">`#FFB81C`](https://commons.wikimedia.org/wiki/File:Flag_of_Jamaica.svg) |
| `jo` | [Jordan](https://en.wikipedia.org/wiki/Jordan) | | | | | |
| `kz` | [Kazakhstan](https://en.wikipedia.org/wiki/Kazakhstan) | <img src="circle/countries/kz.svg" width="32"> | <img src="square/countries/kz.svg" width="32"> | <img src="full-size-simplified/countries/kz.svg" height="20"> | [✓](full-size/countries/kz.svg) | [<img src="swatches/00AFCA.svg" width="12">`#00AFCA`](https://en.wikipedia.org/wiki/File:Flag_of_Kazakhstan.svg)<br>[<img src="swatches/FFD700.svg" width="12">`#FFD700`](https://en.wikipedia.org/wiki/File:Flag_of_Kazakhstan.svg) |
| `ki` | [Kiribati](https://en.wikipedia.org/wiki/Kiribati) | <img src="circle/countries/ki.svg" width="32"> | <img src="square/countries/ki.svg" width="32"> | <img src="full-size-simplified/countries/ki.svg" height="20"> | [✓](full-size/countries/ki.svg) | [<img src="swatches/183070.svg" width="12">`#183070`](https://commons.wikimedia.org/wiki/File:Flag_of_Kiribati.svg)<br>[<img src="swatches/C81010.svg" width="12">`#C81010`](https://commons.wikimedia.org/wiki/File:Flag_of_Kiribati.svg)<br>[<img src="swatches/F8D000.svg" width="12">`#F8D000`](https://commons.wikimedia.org/wiki/File:Flag_of_Kiribati.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Kiribati.svg) |
| `kw` | [Kuwait](https://en.wikipedia.org/wiki/Kuwait) | | | | | |
| `kg` | [Kyrgyzstan](https://en.wikipedia.org/wiki/Kyrgyzstan) | <img src="circle/countries/kg.svg" width="32"> | <img src="square/countries/kg.svg" width="32"> | <img src="full-size-simplified/countries/kg.svg" height="20"> | [✓](full-size/countries/kg.svg) | [<img src="swatches/E8112D.svg" width="12">`#E8112D`](https://en.wikipedia.org/wiki/File:Flag_of_Kyrgyzstan.svg)<br>[<img src="swatches/FFEF00.svg" width="12">`#FFEF00`](https://en.wikipedia.org/wiki/File:Flag_of_Kyrgyzstan.svg) |
| `la` | [Laos](https://en.wikipedia.org/wiki/Laos) | <img src="circle/countries/la.svg" width="32"> | <img src="square/countries/la.svg" width="32"> | <img src="full-size-simplified/countries/la.svg" height="20"> | [✓](full-size/countries/la.svg) | [<img src="swatches/002868.svg" width="12">`#002868`](https://commons.wikimedia.org/wiki/File:Flag_of_Laos.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Laos.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Laos.svg) |
| `lv` | [Latvia](https://en.wikipedia.org/wiki/Latvia) | <img src="circle/countries/lv.svg" width="32"> | <img src="square/countries/lv.svg" width="32"> | <img src="full-size-simplified/countries/lv.svg" height="20"> | [✓](full-size/countries/lv.svg) | [<img src="swatches/9D2235.svg" width="12">`#9D2235`](https://commons.wikimedia.org/wiki/File:Flag_of_Latvia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Latvia.svg) |
| `lb` | [Lebanon](https://en.wikipedia.org/wiki/Lebanon) | | | | | |
| `ls` | [Lesotho](https://en.wikipedia.org/wiki/Lesotho) | <img src="circle/countries/ls.svg" width="32"> | <img src="square/countries/ls.svg" width="32"> | <img src="full-size-simplified/countries/ls.svg" height="20"> | [✓](full-size/countries/ls.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Lesotho.svg)<br>[<img src="swatches/001489.svg" width="12">`#001489`](https://commons.wikimedia.org/wiki/File:Flag_of_Lesotho.svg)<br>[<img src="swatches/009A44.svg" width="12">`#009A44`](https://commons.wikimedia.org/wiki/File:Flag_of_Lesotho.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Lesotho.svg) |
| `lr` | [Liberia](https://en.wikipedia.org/wiki/Liberia) | <img src="circle/countries/lr.svg" width="32"> | <img src="square/countries/lr.svg" width="32"> | <img src="full-size-simplified/countries/lr.svg" height="20"> | [✓](full-size/countries/lr.svg) | [<img src="swatches/003377.svg" width="12">`#003377`](https://commons.wikimedia.org/wiki/File:Flag_of_Liberia.svg)<br>[<img src="swatches/CC1133.svg" width="12">`#CC1133`](https://commons.wikimedia.org/wiki/File:Flag_of_Liberia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Liberia.svg) |
| `ly` | [Libya](https://en.wikipedia.org/wiki/Libya) | | | | | |
| `li` | [Liechtenstein](https://en.wikipedia.org/wiki/Liechtenstein) | | | | | |
| `lt` | [Lithuania](https://en.wikipedia.org/wiki/Lithuania) | <img src="circle/countries/lt.svg" width="32"> | <img src="square/countries/lt.svg" width="32"> | <img src="full-size-simplified/countries/lt.svg" height="20"> | [✓](full-size/countries/lt.svg) | [<img src="swatches/FDB913.svg" width="12">`#FDB913`](https://en.wikipedia.org/wiki/File:Flag_of_Lithuania.svg)<br>[<img src="swatches/006A44.svg" width="12">`#006A44`](https://en.wikipedia.org/wiki/File:Flag_of_Lithuania.svg)<br>[<img src="swatches/C1272D.svg" width="12">`#C1272D`](https://en.wikipedia.org/wiki/File:Flag_of_Lithuania.svg) |
| `lu` | [Luxembourg](https://en.wikipedia.org/wiki/Luxembourg) | <img src="circle/countries/lu.svg" width="32"> | <img src="square/countries/lu.svg" width="32"> | <img src="full-size-simplified/countries/lu.svg" height="20"> | [✓](full-size/countries/lu.svg) | [<img src="swatches/00A3E0.svg" width="12">`#00A3E0`](https://commons.wikimedia.org/wiki/File:Flag_of_Luxembourg.svg)<br>[<img src="swatches/EF3340.svg" width="12">`#EF3340`](https://commons.wikimedia.org/wiki/File:Flag_of_Luxembourg.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Luxembourg.svg) |
| `mg` | [Madagascar](https://en.wikipedia.org/wiki/Madagascar) | <img src="circle/countries/mg.svg" width="32"> | <img src="square/countries/mg.svg" width="32"> | <img src="full-size-simplified/countries/mg.svg" height="20"> | [✓](full-size/countries/mg.svg) | [<img src="swatches/00843D.svg" width="12">`#00843D`](https://commons.wikimedia.org/wiki/File:Flag_of_Madagascar.svg)<br>[<img src="swatches/F9423A.svg" width="12">`#F9423A`](https://commons.wikimedia.org/wiki/File:Flag_of_Madagascar.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Madagascar.svg) |
| `mw` | [Malawi](https://en.wikipedia.org/wiki/Malawi) | <img src="circle/countries/mw.svg" width="32"> | <img src="square/countries/mw.svg" width="32"> | <img src="full-size-simplified/countries/mw.svg" height="20"> | [✓](full-size/countries/mw.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Malawi.svg)<br>[<img src="swatches/339E35.svg" width="12">`#339E35`](https://commons.wikimedia.org/wiki/File:Flag_of_Malawi.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Malawi.svg) |
| `my` | [Malaysia](https://en.wikipedia.org/wiki/Malaysia) | <img src="circle/countries/my.svg" width="32"> | <img src="square/countries/my.svg" width="32"> | <img src="full-size-simplified/countries/my.svg" height="20"> | [✓](full-size/countries/my.svg) | [<img src="swatches/010066.svg" width="12">`#010066`](https://commons.wikimedia.org/wiki/File:Flag_of_Malaysia.svg)<br>[<img src="swatches/CC0001.svg" width="12">`#CC0001`](https://commons.wikimedia.org/wiki/File:Flag_of_Malaysia.svg)<br>[<img src="swatches/FCC200.svg" width="12">`#FCC200`](https://commons.wikimedia.org/wiki/File:Flag_of_Malaysia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Malaysia.svg) |
| `mv` | [Maldives](https://en.wikipedia.org/wiki/Maldives) | | | | | |
| `ml` | [Mali](https://en.wikipedia.org/wiki/Mali) | <img src="circle/countries/ml.svg" width="32"> | <img src="square/countries/ml.svg" width="32"> | <img src="full-size-simplified/countries/ml.svg" height="20"> | [✓](full-size/countries/ml.svg) | [<img src="swatches/14B53A.svg" width="12">`#14B53A`](https://commons.wikimedia.org/wiki/File:Flag_of_Mali.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Mali.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Mali.svg) |
| `mt` | [Malta](https://en.wikipedia.org/wiki/Malta) | <img src="circle/countries/mt.svg" width="32"> | <img src="square/countries/mt.svg" width="32"> | <img src="full-size-simplified/countries/mt.svg" height="20"> | [✓](full-size/countries/mt.svg) | [<img src="swatches/CF142B.svg" width="12">`#CF142B`](https://commons.wikimedia.org/wiki/File:Flag_of_Malta.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Malta.svg) |
| `mh` | [Marshall Islands](https://en.wikipedia.org/wiki/Marshall_Islands) | <img src="circle/countries/mh.svg" width="32"> | <img src="square/countries/mh.svg" width="32"> | <img src="full-size-simplified/countries/mh.svg" height="20"> | [✓](full-size/countries/mh.svg) | [<img src="swatches/003893.svg" width="12">`#003893`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Marshall_Islands.svg)<br>[<img src="swatches/DD7500.svg" width="12">`#DD7500`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Marshall_Islands.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Marshall_Islands.svg) |
| `mr` | [Mauritania](https://en.wikipedia.org/wiki/Mauritania) | | | | | |
| `mu` | [Mauritius](https://en.wikipedia.org/wiki/Mauritius) | <img src="circle/countries/mu.svg" width="32"> | <img src="square/countries/mu.svg" width="32"> | <img src="full-size-simplified/countries/mu.svg" height="20"> | [✓](full-size/countries/mu.svg) | [<img src="swatches/008658.svg" width="12">`#008658`](https://commons.wikimedia.org/wiki/File:Flag_of_Mauritius.svg)<br>[<img src="swatches/2D3359.svg" width="12">`#2D3359`](https://commons.wikimedia.org/wiki/File:Flag_of_Mauritius.svg)<br>[<img src="swatches/D01C1F.svg" width="12">`#D01C1F`](https://commons.wikimedia.org/wiki/File:Flag_of_Mauritius.svg)<br>[<img src="swatches/F7B718.svg" width="12">`#F7B718`](https://commons.wikimedia.org/wiki/File:Flag_of_Mauritius.svg) |
| `mx` | [Mexico](https://en.wikipedia.org/wiki/Mexico) | <img src="circle/countries/mx.svg" width="32"> | <img src="square/countries/mx.svg" width="32"> | <img src="full-size-simplified/countries/mx.svg" height="20"> | [✓](full-size/countries/mx.svg) | [<img src="swatches/006847.svg" width="12">`#006847`](https://commons.wikimedia.org/wiki/File:Flag_of_Mexico.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Mexico.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Mexico.svg) |
| `fm` | [Micronesia](https://en.wikipedia.org/wiki/Federated_States_of_Micronesia) | <img src="circle/countries/fm.svg" width="32"> | <img src="square/countries/fm.svg" width="32"> | <img src="full-size-simplified/countries/fm.svg" height="20"> | [✓](full-size/countries/fm.svg) | [<img src="swatches/75B2DD.svg" width="12">`#75B2DD`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Federated_States_of_Micronesia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Federated_States_of_Micronesia.svg) |
| `md` | [Moldova](https://en.wikipedia.org/wiki/Moldova) | | | | | |
| `mc` | [Monaco](https://en.wikipedia.org/wiki/Monaco) | <img src="circle/countries/mc.svg" width="32"> | <img src="square/countries/mc.svg" width="32"> | <img src="full-size-simplified/countries/mc.svg" height="20"> | [✓](full-size/countries/mc.svg) | [<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Monaco.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Monaco.svg) |
| `mn` | [Mongolia](https://en.wikipedia.org/wiki/Mongolia) | <img src="circle/countries/mn.svg" width="32"> | <img src="square/countries/mn.svg" width="32"> | <img src="full-size-simplified/countries/mn.svg" height="20"> | [✓](full-size/countries/mn.svg) | [<img src="swatches/DA2031.svg" width="12">`#DA2031`](https://en.wikipedia.org/wiki/File:Flag_of_Mongolia.svg)<br>[<img src="swatches/0066B2.svg" width="12">`#0066B2`](https://en.wikipedia.org/wiki/File:Flag_of_Mongolia.svg)<br>[<img src="swatches/FFD300.svg" width="12">`#FFD300`](https://en.wikipedia.org/wiki/File:Flag_of_Mongolia.svg) |
| `me` | [Montenegro](https://en.wikipedia.org/wiki/Montenegro) | | | | | |
| `ma` | [Morocco](https://en.wikipedia.org/wiki/Morocco) | | | | | |
| `mz` | [Mozambique](https://en.wikipedia.org/wiki/Mozambique) | | | | | |
| `mm` | [Myanmar](https://en.wikipedia.org/wiki/Myanmar) | <img src="circle/countries/mm.svg" width="32"> | <img src="square/countries/mm.svg" width="32"> | <img src="full-size-simplified/countries/mm.svg" height="20"> | [✓](full-size/countries/mm.svg) | [<img src="swatches/FECB00.svg" width="12">`#FECB00`](https://en.wikipedia.org/wiki/File:Flag_of_Myanmar.svg)<br>[<img src="swatches/34B233.svg" width="12">`#34B233`](https://en.wikipedia.org/wiki/File:Flag_of_Myanmar.svg)<br>[<img src="swatches/EA2839.svg" width="12">`#EA2839`](https://en.wikipedia.org/wiki/File:Flag_of_Myanmar.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Myanmar.svg) |
| `na` | [Namibia](https://en.wikipedia.org/wiki/Namibia) | <img src="circle/countries/na.svg" width="32"> | <img src="square/countries/na.svg" width="32"> | <img src="full-size-simplified/countries/na.svg" height="20"> | [✓](full-size/countries/na.svg) | [<img src="swatches/002F6C.svg" width="12">`#002F6C`](https://commons.wikimedia.org/wiki/File:Flag_of_Namibia.svg)<br>[<img src="swatches/009A44.svg" width="12">`#009A44`](https://commons.wikimedia.org/wiki/File:Flag_of_Namibia.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Namibia.svg)<br>[<img src="swatches/FFCD00.svg" width="12">`#FFCD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Namibia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Namibia.svg) |
| `nr` | [Nauru](https://en.wikipedia.org/wiki/Nauru) | <img src="circle/countries/nr.svg" width="32"> | <img src="square/countries/nr.svg" width="32"> | <img src="full-size-simplified/countries/nr.svg" height="20"> | [✓](full-size/countries/nr.svg) | [<img src="swatches/012169.svg" width="12">`#012169`](https://commons.wikimedia.org/wiki/File:Flag_of_Nauru.svg)<br>[<img src="swatches/FFC72C.svg" width="12">`#FFC72C`](https://commons.wikimedia.org/wiki/File:Flag_of_Nauru.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Nauru.svg) |
| `np` | [Nepal](https://en.wikipedia.org/wiki/Nepal) | <img src="circle/countries/np.svg" width="32"> | <img src="square/countries/np.svg" width="32"> | <img src="full-size-simplified/countries/np.svg" height="20"> | [✓](full-size/countries/np.svg) | [<img src="swatches/DC143C.svg" width="12">`#DC143C`](https://commons.wikimedia.org/wiki/File:Flag_of_Nepal.svg)<br>[<img src="swatches/003893.svg" width="12">`#003893`](https://commons.wikimedia.org/wiki/File:Flag_of_Nepal.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Nepal.svg) |
| `nl` | [Netherlands](https://en.wikipedia.org/wiki/Netherlands) | <img src="circle/countries/nl.svg" width="32"> | <img src="square/countries/nl.svg" width="32"> | <img src="full-size-simplified/countries/nl.svg" height="20"> | [✓](full-size/countries/nl.svg) | [<img src="swatches/AE1C28.svg" width="12">`#AE1C28`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Netherlands.svg)<br>[<img src="swatches/21468B.svg" width="12">`#21468B`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Netherlands.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Netherlands.svg) |
| `nz` | [New Zealand](https://en.wikipedia.org/wiki/New_Zealand) | <img src="circle/countries/nz.svg" width="32"> | <img src="square/countries/nz.svg" width="32"> | <img src="full-size-simplified/countries/nz.svg" height="20"> | [✓](full-size/countries/nz.svg) | [<img src="swatches/012169.svg" width="12">`#012169`](https://commons.wikimedia.org/wiki/File:Flag_of_New_Zealand.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_New_Zealand.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_New_Zealand.svg) |
| `ni` | [Nicaragua](https://en.wikipedia.org/wiki/Nicaragua) | | | | | |
| `ne` | [Niger](https://en.wikipedia.org/wiki/Niger) | <img src="circle/countries/ne.svg" width="32"> | <img src="square/countries/ne.svg" width="32"> | <img src="full-size-simplified/countries/ne.svg" height="20"> | [✓](full-size/countries/ne.svg) | [<img src="swatches/0DB02B.svg" width="12">`#0DB02B`](https://commons.wikimedia.org/wiki/File:Flag_of_Niger.svg)<br>[<img src="swatches/E05206.svg" width="12">`#E05206`](https://commons.wikimedia.org/wiki/File:Flag_of_Niger.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Niger.svg) |
| `ng` | [Nigeria](https://en.wikipedia.org/wiki/Nigeria) | <img src="circle/countries/ng.svg" width="32"> | <img src="square/countries/ng.svg" width="32"> | <img src="full-size-simplified/countries/ng.svg" height="20"> | [✓](full-size/countries/ng.svg) | [<img src="swatches/008751.svg" width="12">`#008751`](https://commons.wikimedia.org/wiki/File:Flag_of_Nigeria.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Nigeria.svg) |
| `kp` | [North Korea](https://en.wikipedia.org/wiki/North_Korea) | | | | | |
| `mk` | [North Macedonia](https://en.wikipedia.org/wiki/North_Macedonia) | <img src="circle/countries/mk.svg" width="32"> | <img src="square/countries/mk.svg" width="32"> | <img src="full-size-simplified/countries/mk.svg" height="20"> | [✓](full-size/countries/mk.svg) | [<img src="swatches/D82126.svg" width="12">`#D82126`](https://commons.wikimedia.org/wiki/File:Flag_of_North_Macedonia.svg)<br>[<img src="swatches/F8E92E.svg" width="12">`#F8E92E`](https://commons.wikimedia.org/wiki/File:Flag_of_North_Macedonia.svg) |
| `no` | [Norway](https://en.wikipedia.org/wiki/Norway) | <img src="circle/countries/no.svg" width="32"> | <img src="square/countries/no.svg" width="32"> | <img src="full-size-simplified/countries/no.svg" height="20"> | [✓](full-size/countries/no.svg) | [<img src="swatches/BA0C2F.svg" width="12">`#BA0C2F`](https://commons.wikimedia.org/wiki/File:Flag_of_Norway.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Norway.svg)<br>[<img src="swatches/00205B.svg" width="12">`#00205B`](https://commons.wikimedia.org/wiki/File:Flag_of_Norway.svg) |
| `om` | [Oman](https://en.wikipedia.org/wiki/Oman) | | | | | |
| `pk` | [Pakistan](https://en.wikipedia.org/wiki/Pakistan) | <img src="circle/countries/pk.svg" width="32"> | <img src="square/countries/pk.svg" width="32"> | <img src="full-size-simplified/countries/pk.svg" height="20"> | [✓](full-size/countries/pk.svg) | [<img src="swatches/01411C.svg" width="12">`#01411C`](https://commons.wikimedia.org/wiki/File:Flag_of_Pakistan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Pakistan.svg) |
| `pw` | [Palau](https://en.wikipedia.org/wiki/Palau) | <img src="circle/countries/pw.svg" width="32"> | <img src="square/countries/pw.svg" width="32"> | <img src="full-size-simplified/countries/pw.svg" height="20"> | [✓](full-size/countries/pw.svg) | [<img src="swatches/0099FF.svg" width="12">`#0099FF`](https://commons.wikimedia.org/wiki/File:Flag_of_Palau.svg)<br>[<img src="swatches/FFFF00.svg" width="12">`#FFFF00`](https://commons.wikimedia.org/wiki/File:Flag_of_Palau.svg) |
| `pa` | [Panama](https://en.wikipedia.org/wiki/Panama) | | | | | |
| `pg` | [Papua New Guinea](https://en.wikipedia.org/wiki/Papua_New_Guinea) | <img src="circle/countries/pg.svg" width="32"> | <img src="square/countries/pg.svg" width="32"> | <img src="full-size-simplified/countries/pg.svg" height="20"> | [✓](full-size/countries/pg.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Papua_New_Guinea.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Papua_New_Guinea.svg)<br>[<img src="swatches/FFCD00.svg" width="12">`#FFCD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Papua_New_Guinea.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Papua_New_Guinea.svg) |
| `py` | [Paraguay](https://en.wikipedia.org/wiki/Paraguay) | | | | | |
| `pe` | [Peru](https://en.wikipedia.org/wiki/Peru) | | | | | |
| `ph` | [Philippines](https://en.wikipedia.org/wiki/Philippines) | <img src="circle/countries/ph.svg" width="32"> | <img src="square/countries/ph.svg" width="32"> | <img src="full-size-simplified/countries/ph.svg" height="20"> | [✓](full-size/countries/ph.svg) | [<img src="swatches/0038A8.svg" width="12">`#0038A8`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Philippines.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Philippines.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Philippines.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Philippines.svg) |
| `pl` | [Poland](https://en.wikipedia.org/wiki/Poland) | <img src="circle/countries/pl.svg" width="32"> | <img src="square/countries/pl.svg" width="32"> | <img src="full-size-simplified/countries/pl.svg" height="20"> | [✓](full-size/countries/pl.svg) | [<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Poland.svg)<br>[<img src="swatches/DC143C.svg" width="12">`#DC143C`](https://en.wikipedia.org/wiki/File:Flag_of_Poland.svg) |
| `pt` | [Portugal](https://en.wikipedia.org/wiki/Portugal) | <img src="circle/countries/pt.svg" width="32"> | <img src="square/countries/pt.svg" width="32"> | <img src="full-size-simplified/countries/pt.svg" height="20"> | [✓](full-size/countries/pt.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Portugal.svg)<br>[<img src="swatches/003399.svg" width="12">`#003399`](https://commons.wikimedia.org/wiki/File:Flag_of_Portugal.svg)<br>[<img src="swatches/006600.svg" width="12">`#006600`](https://commons.wikimedia.org/wiki/File:Flag_of_Portugal.svg)<br>[<img src="swatches/FF0000.svg" width="12">`#FF0000`](https://commons.wikimedia.org/wiki/File:Flag_of_Portugal.svg)<br>[<img src="swatches/FFFF00.svg" width="12">`#FFFF00`](https://commons.wikimedia.org/wiki/File:Flag_of_Portugal.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Portugal.svg) |
| `qa` | [Qatar](https://en.wikipedia.org/wiki/Qatar) | | | | | |
| `ro` | [Romania](https://en.wikipedia.org/wiki/Romania) | <img src="circle/countries/ro.svg" width="32"> | <img src="square/countries/ro.svg" width="32"> | <img src="full-size-simplified/countries/ro.svg" height="20"> | [✓](full-size/countries/ro.svg) | [<img src="swatches/002B7F.svg" width="12">`#002B7F`](https://commons.wikimedia.org/wiki/File:Flag_of_Romania.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Romania.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Romania.svg) |
| `ru` | [Russia](https://en.wikipedia.org/wiki/Russia) | <img src="circle/countries/ru.svg" width="32"> | <img src="square/countries/ru.svg" width="32"> | <img src="full-size-simplified/countries/ru.svg" height="20"> | [✓](full-size/countries/ru.svg) | [<img src="swatches/0039A6.svg" width="12">`#0039A6`](https://commons.wikimedia.org/wiki/File:Flag_of_Russia.svg)<br>[<img src="swatches/D52B1E.svg" width="12">`#D52B1E`](https://commons.wikimedia.org/wiki/File:Flag_of_Russia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Russia.svg) |
| `rw` | [Rwanda](https://en.wikipedia.org/wiki/Rwanda) | <img src="circle/countries/rw.svg" width="32"> | <img src="square/countries/rw.svg" width="32"> | <img src="full-size-simplified/countries/rw.svg" height="20"> | [✓](full-size/countries/rw.svg) | [<img src="swatches/00A3E0.svg" width="12">`#00A3E0`](https://commons.wikimedia.org/wiki/File:Flag_of_Rwanda.svg)<br>[<img src="swatches/20603D.svg" width="12">`#20603D`](https://commons.wikimedia.org/wiki/File:Flag_of_Rwanda.svg)<br>[<img src="swatches/FAD201.svg" width="12">`#FAD201`](https://commons.wikimedia.org/wiki/File:Flag_of_Rwanda.svg) |
| `kn` | [Saint Kitts and Nevis](https://en.wikipedia.org/wiki/Saint_Kitts_and_Nevis) | <img src="circle/countries/kn.svg" width="32"> | <img src="square/countries/kn.svg" width="32"> | <img src="full-size-simplified/countries/kn.svg" height="20"> | [✓](full-size/countries/kn.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Kitts_and_Nevis.svg)<br>[<img src="swatches/009739.svg" width="12">`#009739`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Kitts_and_Nevis.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Kitts_and_Nevis.svg)<br>[<img src="swatches/FFCD00.svg" width="12">`#FFCD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Kitts_and_Nevis.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Kitts_and_Nevis.svg) |
| `lc` | [Saint Lucia](https://en.wikipedia.org/wiki/Saint_Lucia) | <img src="circle/countries/lc.svg" width="32"> | <img src="square/countries/lc.svg" width="32"> | <img src="full-size-simplified/countries/lc.svg" height="20"> | [✓](full-size/countries/lc.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Lucia.svg)<br>[<img src="swatches/66CCFF.svg" width="12">`#66CCFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Lucia.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Lucia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Lucia.svg) |
| `vc` | [Saint Vincent and the Grenadines](https://en.wikipedia.org/wiki/Saint_Vincent_and_the_Grenadines) | <img src="circle/countries/vc.svg" width="32"> | <img src="square/countries/vc.svg" width="32"> | <img src="full-size-simplified/countries/vc.svg" height="20"> | [✓](full-size/countries/vc.svg) | [<img src="swatches/002674.svg" width="12">`#002674`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Vincent_and_the_Grenadines.svg)<br>[<img src="swatches/007C2E.svg" width="12">`#007C2E`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Vincent_and_the_Grenadines.svg)<br>[<img src="swatches/FCD022.svg" width="12">`#FCD022`](https://commons.wikimedia.org/wiki/File:Flag_of_Saint_Vincent_and_the_Grenadines.svg) |
| `ws` | [Samoa](https://en.wikipedia.org/wiki/Samoa) | <img src="circle/countries/ws.svg" width="32"> | <img src="square/countries/ws.svg" width="32"> | <img src="full-size-simplified/countries/ws.svg" height="20"> | [✓](full-size/countries/ws.svg) | [<img src="swatches/002B7F.svg" width="12">`#002B7F`](https://commons.wikimedia.org/wiki/File:Flag_of_Samoa.svg)<br>[<img src="swatches/CE1126.svg" width="12">`#CE1126`](https://commons.wikimedia.org/wiki/File:Flag_of_Samoa.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Samoa.svg) |
| `sm` | [San Marino](https://en.wikipedia.org/wiki/San_Marino) | | | | | |
| `sa` | [Saudi Arabia](https://en.wikipedia.org/wiki/Saudi_Arabia) | <img src="circle/countries/sa.svg" width="32"> | <img src="square/countries/sa.svg" width="32"> | <img src="full-size-simplified/countries/sa.svg" height="20"> | [✓](full-size/countries/sa.svg) | [<img src="swatches/005430.svg" width="12">`#005430`](https://en.wikipedia.org/wiki/File:Flag_of_Saudi_Arabia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Saudi_Arabia.svg) |
| `sn` | [Senegal](https://en.wikipedia.org/wiki/Senegal) | <img src="circle/countries/sn.svg" width="32"> | <img src="square/countries/sn.svg" width="32"> | <img src="full-size-simplified/countries/sn.svg" height="20"> | [✓](full-size/countries/sn.svg) | [<img src="swatches/00853F.svg" width="12">`#00853F`](https://commons.wikimedia.org/wiki/File:Flag_of_Senegal.svg)<br>[<img src="swatches/E31B23.svg" width="12">`#E31B23`](https://commons.wikimedia.org/wiki/File:Flag_of_Senegal.svg)<br>[<img src="swatches/FDEF42.svg" width="12">`#FDEF42`](https://commons.wikimedia.org/wiki/File:Flag_of_Senegal.svg) |
| `rs` | [Serbia](https://en.wikipedia.org/wiki/Serbia) | <img src="circle/countries/rs.svg" width="32"> | <img src="square/countries/rs.svg" width="32"> | <img src="full-size-simplified/countries/rs.svg" height="20"> | [✓](full-size/countries/rs.svg) | [<img src="swatches/0C4076.svg" width="12">`#0C4076`](https://commons.wikimedia.org/wiki/File:Flag_of_Serbia.svg)<br>[<img src="swatches/21231E.svg" width="12">`#21231E`](https://commons.wikimedia.org/wiki/File:Flag_of_Serbia.svg)<br>[<img src="swatches/C6363C.svg" width="12">`#C6363C`](https://commons.wikimedia.org/wiki/File:Flag_of_Serbia.svg)<br>[<img src="swatches/EDB92E.svg" width="12">`#EDB92E`](https://commons.wikimedia.org/wiki/File:Flag_of_Serbia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Serbia.svg) |
| `sc` | [Seychelles](https://en.wikipedia.org/wiki/Seychelles) | <img src="circle/countries/sc.svg" width="32"> | <img src="square/countries/sc.svg" width="32"> | <img src="full-size-simplified/countries/sc.svg" height="20"> | [✓](full-size/countries/sc.svg) | [<img src="swatches/002F6C.svg" width="12">`#002F6C`](https://commons.wikimedia.org/wiki/File:Flag_of_Seychelles.svg)<br>[<img src="swatches/007A33.svg" width="12">`#007A33`](https://commons.wikimedia.org/wiki/File:Flag_of_Seychelles.svg)<br>[<img src="swatches/D22730.svg" width="12">`#D22730`](https://commons.wikimedia.org/wiki/File:Flag_of_Seychelles.svg)<br>[<img src="swatches/FED141.svg" width="12">`#FED141`](https://commons.wikimedia.org/wiki/File:Flag_of_Seychelles.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Seychelles.svg) |
| `sl` | [Sierra Leone](https://en.wikipedia.org/wiki/Sierra_Leone) | <img src="circle/countries/sl.svg" width="32"> | <img src="square/countries/sl.svg" width="32"> | <img src="full-size-simplified/countries/sl.svg" height="20"> | [✓](full-size/countries/sl.svg) | [<img src="swatches/0072C6.svg" width="12">`#0072C6`](https://commons.wikimedia.org/wiki/File:Flag_of_Sierra_Leone.svg)<br>[<img src="swatches/1EB53A.svg" width="12">`#1EB53A`](https://commons.wikimedia.org/wiki/File:Flag_of_Sierra_Leone.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Sierra_Leone.svg) |
| `sg` | [Singapore](https://en.wikipedia.org/wiki/Singapore) | <img src="circle/countries/sg.svg" width="32"> | <img src="square/countries/sg.svg" width="32"> | <img src="full-size-simplified/countries/sg.svg" height="20"> | [✓](full-size/countries/sg.svg) | [<img src="swatches/ED2939.svg" width="12">`#ED2939`](https://commons.wikimedia.org/wiki/File:Flag_of_Singapore.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Singapore.svg) |
| `sk` | [Slovakia](https://en.wikipedia.org/wiki/Slovakia) | <img src="circle/countries/sk.svg" width="32"> | <img src="square/countries/sk.svg" width="32"> | <img src="full-size-simplified/countries/sk.svg" height="20"> | [✓](full-size/countries/sk.svg) | [<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovakia.svg)<br>[<img src="swatches/254AA5.svg" width="12">`#254AA5`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovakia.svg)<br>[<img src="swatches/ED1C24.svg" width="12">`#ED1C24`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovakia.svg) |
| `si` | [Slovenia](https://en.wikipedia.org/wiki/Slovenia) | <img src="circle/countries/si.svg" width="32"> | <img src="square/countries/si.svg" width="32"> | <img src="full-size-simplified/countries/si.svg" height="20"> | [✓](full-size/countries/si.svg) | [<img src="swatches/003DA5.svg" width="12">`#003DA5`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovenia.svg)<br>[<img src="swatches/ED1C24.svg" width="12">`#ED1C24`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovenia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovenia.svg)<br>[<img src="swatches/FFD700.svg" width="12">`#FFD700`](https://commons.wikimedia.org/wiki/File:Flag_of_Slovenia.svg) |
| `sb` | [Solomon Islands](https://en.wikipedia.org/wiki/Solomon_Islands) | <img src="circle/countries/sb.svg" width="32"> | <img src="square/countries/sb.svg" width="32"> | <img src="full-size-simplified/countries/sb.svg" height="20"> | [✓](full-size/countries/sb.svg) | [<img src="swatches/0051BA.svg" width="12">`#0051BA`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Solomon_Islands.svg)<br>[<img src="swatches/215B33.svg" width="12">`#215B33`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Solomon_Islands.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Solomon_Islands.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Solomon_Islands.svg) |
| `so` | [Somalia](https://en.wikipedia.org/wiki/Somalia) | <img src="circle/countries/so.svg" width="32"> | <img src="square/countries/so.svg" width="32"> | <img src="full-size-simplified/countries/so.svg" height="20"> | [✓](full-size/countries/so.svg) | [<img src="swatches/4189DD.svg" width="12">`#4189DD`](https://commons.wikimedia.org/wiki/File:Flag_of_Somalia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Somalia.svg) |
| `za` | [South Africa](https://en.wikipedia.org/wiki/South_Africa) | <img src="circle/countries/za.svg" width="32"> | <img src="square/countries/za.svg" width="32"> | <img src="full-size-simplified/countries/za.svg" height="20"> | [✓](full-size/countries/za.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Africa.svg)<br>[<img src="swatches/001489.svg" width="12">`#001489`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Africa.svg)<br>[<img src="swatches/007749.svg" width="12">`#007749`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Africa.svg)<br>[<img src="swatches/E03C31.svg" width="12">`#E03C31`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Africa.svg)<br>[<img src="swatches/FFB81C.svg" width="12">`#FFB81C`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Africa.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Africa.svg) |
| `kr` | [South Korea](https://en.wikipedia.org/wiki/South_Korea) | <img src="circle/countries/kr.svg" width="32"> | <img src="square/countries/kr.svg" width="32"> | <img src="full-size-simplified/countries/kr.svg" height="20"> | [✓](full-size/countries/kr.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Korea.svg)<br>[<img src="swatches/0047A0.svg" width="12">`#0047A0`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Korea.svg)<br>[<img src="swatches/CD2E3A.svg" width="12">`#CD2E3A`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Korea.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Korea.svg) |
| `ss` | [South Sudan](https://en.wikipedia.org/wiki/South_Sudan) | <img src="circle/countries/ss.svg" width="32"> | <img src="square/countries/ss.svg" width="32"> | <img src="full-size-simplified/countries/ss.svg" height="20"> | [✓](full-size/countries/ss.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Sudan.svg)<br>[<img src="swatches/00914C.svg" width="12">`#00914C`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Sudan.svg)<br>[<img src="swatches/00B6F2.svg" width="12">`#00B6F2`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Sudan.svg)<br>[<img src="swatches/E22028.svg" width="12">`#E22028`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Sudan.svg)<br>[<img src="swatches/FFE51A.svg" width="12">`#FFE51A`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Sudan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_South_Sudan.svg) |
| `es` | [Spain](https://en.wikipedia.org/wiki/Spain) | <img src="circle/countries/es.svg" width="32"> | <img src="square/countries/es.svg" width="32"> | <img src="full-size-simplified/countries/es.svg" height="20"> | [✓](full-size/countries/es.svg) | [<img src="swatches/AD1519.svg" width="12">`#AD1519`](https://commons.wikimedia.org/wiki/File:Flag_of_Spain.svg)<br>[<img src="swatches/FABD00.svg" width="12">`#FABD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Spain.svg)<br>[<img src="swatches/C8B100.svg" width="12">`#C8B100`](https://commons.wikimedia.org/wiki/File:Flag_of_Spain.svg)<br>[<img src="swatches/005BBF.svg" width="12">`#005BBF`](https://commons.wikimedia.org/wiki/File:Flag_of_Spain.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Spain.svg) |
| `lk` | [Sri Lanka](https://en.wikipedia.org/wiki/Sri_Lanka) | | | | | |
| `sd` | [Sudan](https://en.wikipedia.org/wiki/Sudan) | <img src="circle/countries/sd.svg" width="32"> | <img src="square/countries/sd.svg" width="32"> | <img src="full-size-simplified/countries/sd.svg" height="20"> | [✓](full-size/countries/sd.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Sudan.svg)<br>[<img src="swatches/007229.svg" width="12">`#007229`](https://commons.wikimedia.org/wiki/File:Flag_of_Sudan.svg)<br>[<img src="swatches/D21034.svg" width="12">`#D21034`](https://commons.wikimedia.org/wiki/File:Flag_of_Sudan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Sudan.svg) |
| `sr` | [Suriname](https://en.wikipedia.org/wiki/Suriname) | | | | | |
| `se` | [Sweden](https://en.wikipedia.org/wiki/Sweden) | <img src="circle/countries/se.svg" width="32"> | <img src="square/countries/se.svg" width="32"> | <img src="full-size-simplified/countries/se.svg" height="20"> | [✓](full-size/countries/se.svg) | [<img src="swatches/005293.svg" width="12">`#005293`](https://commons.wikimedia.org/wiki/File:Flag_of_Sweden.svg)<br>[<img src="swatches/FECB00.svg" width="12">`#FECB00`](https://commons.wikimedia.org/wiki/File:Flag_of_Sweden.svg) |
| `ch` | [Switzerland](https://en.wikipedia.org/wiki/Switzerland) | <img src="circle/countries/ch.svg" width="32"> | <img src="square/countries/ch.svg" width="32"> | <img src="full-size-simplified/countries/ch.svg" height="20"> | [✓](full-size/countries/ch.svg) | [<img src="swatches/FF0000.svg" width="12">`#FF0000`](https://commons.wikimedia.org/wiki/File:Flag_of_Switzerland.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Switzerland.svg) |
| `sy` | [Syria](https://en.wikipedia.org/wiki/Syria) | | | | | |
| `st` | [São Tomé and Príncipe](https://en.wikipedia.org/wiki/S%C3%A3o_Tom%C3%A9_and_Pr%C3%ADncipe) | | | | | |
| `tj` | [Tajikistan](https://en.wikipedia.org/wiki/Tajikistan) | <img src="circle/countries/tj.svg" width="32"> | <img src="square/countries/tj.svg" width="32"> | <img src="full-size-simplified/countries/tj.svg" height="20"> | [✓](full-size/countries/tj.svg) | [<img src="swatches/DC161D.svg" width="12">`#DC161D`](https://en.wikipedia.org/wiki/File:Flag_of_Tajikistan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Tajikistan.svg)<br>[<img src="swatches/197B30.svg" width="12">`#197B30`](https://en.wikipedia.org/wiki/File:Flag_of_Tajikistan.svg)<br>[<img src="swatches/F7BF00.svg" width="12">`#F7BF00`](https://en.wikipedia.org/wiki/File:Flag_of_Tajikistan.svg) |
| `tz` | [Tanzania](https://en.wikipedia.org/wiki/Tanzania) | <img src="circle/countries/tz.svg" width="32"> | <img src="square/countries/tz.svg" width="32"> | <img src="full-size-simplified/countries/tz.svg" height="20"> | [✓](full-size/countries/tz.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Tanzania.svg)<br>[<img src="swatches/00A3DD.svg" width="12">`#00A3DD`](https://commons.wikimedia.org/wiki/File:Flag_of_Tanzania.svg)<br>[<img src="swatches/1EB53A.svg" width="12">`#1EB53A`](https://commons.wikimedia.org/wiki/File:Flag_of_Tanzania.svg)<br>[<img src="swatches/FCD116.svg" width="12">`#FCD116`](https://commons.wikimedia.org/wiki/File:Flag_of_Tanzania.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Tanzania.svg) |
| `th` | [Thailand](https://en.wikipedia.org/wiki/Thailand) | <img src="circle/countries/th.svg" width="32"> | <img src="square/countries/th.svg" width="32"> | <img src="full-size-simplified/countries/th.svg" height="20"> | [✓](full-size/countries/th.svg) | [<img src="swatches/A51931.svg" width="12">`#A51931`](https://en.wikipedia.org/wiki/File:Flag_of_Thailand.svg)<br>[<img src="swatches/F4F5F8.svg" width="12">`#F4F5F8`](https://en.wikipedia.org/wiki/File:Flag_of_Thailand.svg)<br>[<img src="swatches/2D2A4A.svg" width="12">`#2D2A4A`](https://en.wikipedia.org/wiki/File:Flag_of_Thailand.svg) |
| `tl` | [Timor-Leste](https://en.wikipedia.org/wiki/East_Timor) | | | | | |
| `tg` | [Togo](https://en.wikipedia.org/wiki/Togo) | <img src="circle/countries/tg.svg" width="32"> | <img src="square/countries/tg.svg" width="32"> | <img src="full-size-simplified/countries/tg.svg" height="20"> | [✓](full-size/countries/tg.svg) | [<img src="swatches/006A4E.svg" width="12">`#006A4E`](https://commons.wikimedia.org/wiki/File:Flag_of_Togo.svg)<br>[<img src="swatches/D21034.svg" width="12">`#D21034`](https://commons.wikimedia.org/wiki/File:Flag_of_Togo.svg)<br>[<img src="swatches/FFCE00.svg" width="12">`#FFCE00`](https://commons.wikimedia.org/wiki/File:Flag_of_Togo.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Togo.svg) |
| `to` | [Tonga](https://en.wikipedia.org/wiki/Tonga) | <img src="circle/countries/to.svg" width="32"> | <img src="square/countries/to.svg" width="32"> | <img src="full-size-simplified/countries/to.svg" height="20"> | [✓](full-size/countries/to.svg) | [<img src="swatches/C10000.svg" width="12">`#C10000`](https://commons.wikimedia.org/wiki/File:Flag_of_Tonga.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Tonga.svg) |
| `tt` | [Trinidad and Tobago](https://en.wikipedia.org/wiki/Trinidad_and_Tobago) | <img src="circle/countries/tt.svg" width="32"> | <img src="square/countries/tt.svg" width="32"> | <img src="full-size-simplified/countries/tt.svg" height="20"> | [✓](full-size/countries/tt.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Trinidad_and_Tobago.svg)<br>[<img src="swatches/DA1A35.svg" width="12">`#DA1A35`](https://commons.wikimedia.org/wiki/File:Flag_of_Trinidad_and_Tobago.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Trinidad_and_Tobago.svg) |
| `tn` | [Tunisia](https://en.wikipedia.org/wiki/Tunisia) | <img src="circle/countries/tn.svg" width="32"> | <img src="square/countries/tn.svg" width="32"> | <img src="full-size-simplified/countries/tn.svg" height="20"> | [✓](full-size/countries/tn.svg) | [<img src="swatches/E70013.svg" width="12">`#E70013`](https://commons.wikimedia.org/wiki/File:Flag_of_Tunisia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Tunisia.svg) |
| `tr` | [Turkey](https://en.wikipedia.org/wiki/Turkey) | <img src="circle/countries/tr.svg" width="32"> | <img src="square/countries/tr.svg" width="32"> | <img src="full-size-simplified/countries/tr.svg" height="20"> | [✓](full-size/countries/tr.svg) | [<img src="swatches/E30A17.svg" width="12">`#E30A17`](https://en.wikipedia.org/wiki/File:Flag_of_Turkey.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Turkey.svg) |
| `tm` | [Turkmenistan](https://en.wikipedia.org/wiki/Turkmenistan) | <img src="circle/countries/tm.svg" width="32"> | <img src="square/countries/tm.svg" width="32"> | <img src="full-size-simplified/countries/tm.svg" height="20"> | [✓](full-size/countries/tm.svg) | [<img src="swatches/00843D.svg" width="12">`#00843D`](https://en.wikipedia.org/wiki/File:Flag_of_Turkmenistan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Turkmenistan.svg)<br>[<img src="swatches/D22630.svg" width="12">`#D22630`](https://en.wikipedia.org/wiki/File:Flag_of_Turkmenistan.svg)<br>[<img src="swatches/FFC72C.svg" width="12">`#FFC72C`](https://en.wikipedia.org/wiki/File:Flag_of_Turkmenistan.svg)<br>[<img src="swatches/383739.svg" width="12">`#383739`](https://en.wikipedia.org/wiki/File:Flag_of_Turkmenistan.svg) |
| `tv` | [Tuvalu](https://en.wikipedia.org/wiki/Tuvalu) | <img src="circle/countries/tv.svg" width="32"> | <img src="square/countries/tv.svg" width="32"> | <img src="full-size-simplified/countries/tv.svg" height="20"> | [✓](full-size/countries/tv.svg) | [<img src="swatches/009CDE.svg" width="12">`#009CDE`](https://commons.wikimedia.org/wiki/File:Flag_of_Tuvalu.svg)<br>[<img src="swatches/012169.svg" width="12">`#012169`](https://commons.wikimedia.org/wiki/File:Flag_of_Tuvalu.svg)<br>[<img src="swatches/C8102E.svg" width="12">`#C8102E`](https://commons.wikimedia.org/wiki/File:Flag_of_Tuvalu.svg)<br>[<img src="swatches/FEDD00.svg" width="12">`#FEDD00`](https://commons.wikimedia.org/wiki/File:Flag_of_Tuvalu.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Tuvalu.svg) |
| `ug` | [Uganda](https://en.wikipedia.org/wiki/Uganda) | <img src="circle/countries/ug.svg" width="32"> | <img src="square/countries/ug.svg" width="32"> | <img src="full-size-simplified/countries/ug.svg" height="20"> | [✓](full-size/countries/ug.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Uganda.svg)<br>[<img src="swatches/D90000.svg" width="12">`#D90000`](https://commons.wikimedia.org/wiki/File:Flag_of_Uganda.svg)<br>[<img src="swatches/FCDC04.svg" width="12">`#FCDC04`](https://commons.wikimedia.org/wiki/File:Flag_of_Uganda.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Uganda.svg) |
| `ua` | [Ukraine](https://en.wikipedia.org/wiki/Ukraine) | <img src="circle/countries/ua.svg" width="32"> | <img src="square/countries/ua.svg" width="32"> | <img src="full-size-simplified/countries/ua.svg" height="20"> | [✓](full-size/countries/ua.svg) | [<img src="swatches/0057B7.svg" width="12">`#0057B7`](https://en.wikipedia.org/wiki/File:Flag_of_Ukraine.svg)<br>[<img src="swatches/FFD700.svg" width="12">`#FFD700`](https://en.wikipedia.org/wiki/File:Flag_of_Ukraine.svg) |
| `ae` | [United Arab Emirates](https://en.wikipedia.org/wiki/United_Arab_Emirates) | | | | | |
| `uy` | [Uruguay](https://en.wikipedia.org/wiki/Uruguay) | | | | | |
| `uz` | [Uzbekistan](https://en.wikipedia.org/wiki/Uzbekistan) | <img src="circle/countries/uz.svg" width="32"> | <img src="square/countries/uz.svg" width="32"> | <img src="full-size-simplified/countries/uz.svg" height="20"> | [✓](full-size/countries/uz.svg) | [<img src="swatches/3081F7.svg" width="12">`#3081F7`](https://en.wikipedia.org/wiki/File:Flag_of_Uzbekistan.svg)<br>[<img src="swatches/308738.svg" width="12">`#308738`](https://en.wikipedia.org/wiki/File:Flag_of_Uzbekistan.svg)<br>[<img src="swatches/EE162E.svg" width="12">`#EE162E`](https://en.wikipedia.org/wiki/File:Flag_of_Uzbekistan.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_Uzbekistan.svg) |
| `vu` | [Vanuatu](https://en.wikipedia.org/wiki/Vanuatu) | <img src="circle/countries/vu.svg" width="32"> | <img src="square/countries/vu.svg" width="32"> | <img src="full-size-simplified/countries/vu.svg" height="20"> | [✓](full-size/countries/vu.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Vanuatu.svg)<br>[<img src="swatches/009543.svg" width="12">`#009543`](https://commons.wikimedia.org/wiki/File:Flag_of_Vanuatu.svg)<br>[<img src="swatches/D21034.svg" width="12">`#D21034`](https://commons.wikimedia.org/wiki/File:Flag_of_Vanuatu.svg)<br>[<img src="swatches/FDCE12.svg" width="12">`#FDCE12`](https://commons.wikimedia.org/wiki/File:Flag_of_Vanuatu.svg) |
| `ve` | [Venezuela](https://en.wikipedia.org/wiki/Venezuela) | | | | | |
| `vn` | [Vietnam](https://en.wikipedia.org/wiki/Vietnam) | <img src="circle/countries/vn.svg" width="32"> | <img src="square/countries/vn.svg" width="32"> | <img src="full-size-simplified/countries/vn.svg" height="20"> | [✓](full-size/countries/vn.svg) | [<img src="swatches/DA251D.svg" width="12">`#DA251D`](https://en.wikipedia.org/wiki/File:Flag_of_Vietnam.svg)<br>[<img src="swatches/FFFF00.svg" width="12">`#FFFF00`](https://en.wikipedia.org/wiki/File:Flag_of_Vietnam.svg) |
| `ye` | [Yemen](https://en.wikipedia.org/wiki/Yemen) | | | | | |
| `zm` | [Zambia](https://en.wikipedia.org/wiki/Zambia) | <img src="circle/countries/zm.svg" width="32"> | <img src="square/countries/zm.svg" width="32"> | <img src="full-size-simplified/countries/zm.svg" height="20"> | [✓](full-size/countries/zm.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Zambia.svg)<br>[<img src="swatches/147F55.svg" width="12">`#147F55`](https://commons.wikimedia.org/wiki/File:Flag_of_Zambia.svg)<br>[<img src="swatches/D40829.svg" width="12">`#D40829`](https://commons.wikimedia.org/wiki/File:Flag_of_Zambia.svg)<br>[<img src="swatches/F99815.svg" width="12">`#F99815`](https://commons.wikimedia.org/wiki/File:Flag_of_Zambia.svg) |
| `zw` | [Zimbabwe](https://en.wikipedia.org/wiki/Zimbabwe) | <img src="circle/countries/zw.svg" width="32"> | <img src="square/countries/zw.svg" width="32"> | <img src="full-size-simplified/countries/zw.svg" height="20"> | [✓](full-size/countries/zw.svg) | [<img src="swatches/000000.svg" width="12">`#000000`](https://commons.wikimedia.org/wiki/File:Flag_of_Zimbabwe.svg)<br>[<img src="swatches/006400.svg" width="12">`#006400`](https://commons.wikimedia.org/wiki/File:Flag_of_Zimbabwe.svg)<br>[<img src="swatches/D40000.svg" width="12">`#D40000`](https://commons.wikimedia.org/wiki/File:Flag_of_Zimbabwe.svg)<br>[<img src="swatches/FFD200.svg" width="12">`#FFD200`](https://commons.wikimedia.org/wiki/File:Flag_of_Zimbabwe.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Zimbabwe.svg) |

### Languages

A base language flag (e.g. `en`) is a copy of its primary country flag (English → GB). Locale variants (e.g. `en-us`) use a diagonal split: top-left triangle shows the locale country flag, bottom-right shows the base language flag.

#### Base languages

| Code | Name | Circle | Square |
|------|------|:------:|:------:|
| `af` | Afrikaans | <img src="circle/languages/af.svg" width="32"> | <img src="square/languages/af.svg" width="32"> |
| `am` | Amharic | <img src="circle/languages/am.svg" width="32"> | <img src="square/languages/am.svg" width="32"> |
| `ar` | Arabic | <img src="circle/languages/ar.svg" width="32"> | <img src="square/languages/ar.svg" width="32"> |
| `az` | Azerbaijani | <img src="circle/languages/az.svg" width="32"> | <img src="square/languages/az.svg" width="32"> |
| `be` | Belarusian | <img src="circle/languages/be.svg" width="32"> | <img src="square/languages/be.svg" width="32"> |
| `bn` | Bengali | <img src="circle/languages/bn.svg" width="32"> | <img src="square/languages/bn.svg" width="32"> |
| `bs` | Bosnian | <img src="circle/languages/bs.svg" width="32"> | <img src="square/languages/bs.svg" width="32"> |
| `cs` | Czech | <img src="circle/languages/cs.svg" width="32"> | <img src="square/languages/cs.svg" width="32"> |
| `da` | Danish | <img src="circle/languages/da.svg" width="32"> | <img src="square/languages/da.svg" width="32"> |
| `de` | German | <img src="circle/languages/de.svg" width="32"> | <img src="square/languages/de.svg" width="32"> |
| `el` | Greek | <img src="circle/languages/el.svg" width="32"> | <img src="square/languages/el.svg" width="32"> |
| `en` | English | <img src="circle/languages/en.svg" width="32"> | <img src="square/languages/en.svg" width="32"> |
| `es` | Spanish | <img src="circle/languages/es.svg" width="32"> | <img src="square/languages/es.svg" width="32"> |
| `et` | Estonian | <img src="circle/languages/et.svg" width="32"> | <img src="square/languages/et.svg" width="32"> |
| `fa` | Persian | <img src="circle/languages/fa.svg" width="32"> | <img src="square/languages/fa.svg" width="32"> |
| `fi` | Finnish | <img src="circle/languages/fi.svg" width="32"> | <img src="square/languages/fi.svg" width="32"> |
| `fr` | French | <img src="circle/languages/fr.svg" width="32"> | <img src="square/languages/fr.svg" width="32"> |
| `ga` | Irish | <img src="circle/languages/ga.svg" width="32"> | <img src="square/languages/ga.svg" width="32"> |
| `he` | Hebrew | <img src="circle/languages/he.svg" width="32"> | <img src="square/languages/he.svg" width="32"> |
| `hi` | Hindi | <img src="circle/languages/hi.svg" width="32"> | <img src="square/languages/hi.svg" width="32"> |
| `hr` | Croatian | <img src="circle/languages/hr.svg" width="32"> | <img src="square/languages/hr.svg" width="32"> |
| `hu` | Hungarian | <img src="circle/languages/hu.svg" width="32"> | <img src="square/languages/hu.svg" width="32"> |
| `id` | Indonesian | <img src="circle/languages/id.svg" width="32"> | <img src="square/languages/id.svg" width="32"> |
| `is` | Icelandic | <img src="circle/languages/is.svg" width="32"> | <img src="square/languages/is.svg" width="32"> |
| `it` | Italian | <img src="circle/languages/it.svg" width="32"> | <img src="square/languages/it.svg" width="32"> |
| `ja` | Japanese | <img src="circle/languages/ja.svg" width="32"> | <img src="square/languages/ja.svg" width="32"> |
| `ka` | Georgian | <img src="circle/languages/ka.svg" width="32"> | <img src="square/languages/ka.svg" width="32"> |
| `kk` | Kazakh | <img src="circle/languages/kk.svg" width="32"> | <img src="square/languages/kk.svg" width="32"> |
| `km` | Khmer | <img src="circle/languages/km.svg" width="32"> | <img src="square/languages/km.svg" width="32"> |
| `ko` | Korean | <img src="circle/languages/ko.svg" width="32"> | <img src="square/languages/ko.svg" width="32"> |
| `ky` | Kyrgyz | <img src="circle/languages/ky.svg" width="32"> | <img src="square/languages/ky.svg" width="32"> |
| `lo` | Lao | <img src="circle/languages/lo.svg" width="32"> | <img src="square/languages/lo.svg" width="32"> |
| `lt` | Lithuanian | <img src="circle/languages/lt.svg" width="32"> | <img src="square/languages/lt.svg" width="32"> |
| `lv` | Latvian | <img src="circle/languages/lv.svg" width="32"> | <img src="square/languages/lv.svg" width="32"> |
| `mg` | Malagasy | <img src="circle/languages/mg.svg" width="32"> | <img src="square/languages/mg.svg" width="32"> |
| `mk` | Macedonian | <img src="circle/languages/mk.svg" width="32"> | <img src="square/languages/mk.svg" width="32"> |
| `mn` | Mongolian | <img src="circle/languages/mn.svg" width="32"> | <img src="square/languages/mn.svg" width="32"> |
| `ms` | Malay | <img src="circle/languages/ms.svg" width="32"> | <img src="square/languages/ms.svg" width="32"> |
| `mt` | Maltese | <img src="circle/languages/mt.svg" width="32"> | <img src="square/languages/mt.svg" width="32"> |
| `my` | Burmese | <img src="circle/languages/my.svg" width="32"> | <img src="square/languages/my.svg" width="32"> |
| `ne` | Nepali | <img src="circle/languages/ne.svg" width="32"> | <img src="square/languages/ne.svg" width="32"> |
| `nl` | Dutch | <img src="circle/languages/nl.svg" width="32"> | <img src="square/languages/nl.svg" width="32"> |
| `no` | Norwegian | <img src="circle/languages/no.svg" width="32"> | <img src="square/languages/no.svg" width="32"> |
| `pl` | Polish | <img src="circle/languages/pl.svg" width="32"> | <img src="square/languages/pl.svg" width="32"> |
| `ps` | Pashto | <img src="circle/languages/ps.svg" width="32"> | <img src="square/languages/ps.svg" width="32"> |
| `pt` | Portuguese | <img src="circle/languages/pt.svg" width="32"> | <img src="square/languages/pt.svg" width="32"> |
| `ro` | Romanian | <img src="circle/languages/ro.svg" width="32"> | <img src="square/languages/ro.svg" width="32"> |
| `ru` | Russian | <img src="circle/languages/ru.svg" width="32"> | <img src="square/languages/ru.svg" width="32"> |
| `sk` | Slovak | <img src="circle/languages/sk.svg" width="32"> | <img src="square/languages/sk.svg" width="32"> |
| `sl` | Slovenian | <img src="circle/languages/sl.svg" width="32"> | <img src="square/languages/sl.svg" width="32"> |
| `so` | Somali | <img src="circle/languages/so.svg" width="32"> | <img src="square/languages/so.svg" width="32"> |
| `sq` | Albanian | <img src="circle/languages/sq.svg" width="32"> | <img src="square/languages/sq.svg" width="32"> |
| `sr` | Serbian | <img src="circle/languages/sr.svg" width="32"> | <img src="square/languages/sr.svg" width="32"> |
| `sv` | Swedish | <img src="circle/languages/sv.svg" width="32"> | <img src="square/languages/sv.svg" width="32"> |
| `sw` | Swahili | <img src="circle/languages/sw.svg" width="32"> | <img src="square/languages/sw.svg" width="32"> |
| `tg` | Tajik | <img src="circle/languages/tg.svg" width="32"> | <img src="square/languages/tg.svg" width="32"> |
| `th` | Thai | <img src="circle/languages/th.svg" width="32"> | <img src="square/languages/th.svg" width="32"> |
| `tk` | Turkmen | <img src="circle/languages/tk.svg" width="32"> | <img src="square/languages/tk.svg" width="32"> |
| `tl` | Tagalog | <img src="circle/languages/tl.svg" width="32"> | <img src="square/languages/tl.svg" width="32"> |
| `tr` | Turkish | <img src="circle/languages/tr.svg" width="32"> | <img src="square/languages/tr.svg" width="32"> |
| `uk` | Ukrainian | <img src="circle/languages/uk.svg" width="32"> | <img src="square/languages/uk.svg" width="32"> |
| `ur` | Urdu | <img src="circle/languages/ur.svg" width="32"> | <img src="square/languages/ur.svg" width="32"> |
| `uz` | Uzbek | <img src="circle/languages/uz.svg" width="32"> | <img src="square/languages/uz.svg" width="32"> |
| `vi` | Vietnamese | <img src="circle/languages/vi.svg" width="32"> | <img src="square/languages/vi.svg" width="32"> |
| `zh` | Chinese | <img src="circle/languages/zh.svg" width="32"> | <img src="square/languages/zh.svg" width="32"> |

#### Locale variants

| Code | Name | Circle | Square |
|------|------|:------:|:------:|
| `en-us` | English (US) | <img src="circle/languages/en-us.svg" width="32"> | <img src="square/languages/en-us.svg" width="32"> |
| `es-mx` | Spanish (Mexico) | <img src="circle/languages/es-mx.svg" width="32"> | <img src="square/languages/es-mx.svg" width="32"> |
| `fr-ca` | French (Canada) | <img src="circle/languages/fr-ca.svg" width="32"> | <img src="square/languages/fr-ca.svg" width="32"> |
| `fr-ca-qc` | French (Quebec) | <img src="circle/languages/fr-ca-qc.svg" width="32"> | <img src="square/languages/fr-ca-qc.svg" width="32"> |

### Other locales (non-UN entities)

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `northern-cyprus` | [Northern Cyprus](https://en.wikipedia.org/wiki/Northern_Cyprus) | <img src="circle/other/locales/northern-cyprus.svg" width="32"> | <img src="square/other/locales/northern-cyprus.svg" width="32"> | <img src="full-size-simplified/other/locales/northern-cyprus.svg" height="20"> | [✓](full-size/other/locales/northern-cyprus.svg) | [<img src="swatches/E30A17.svg" width="12">`#E30A17`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Turkish_Republic_of_Northern_Cyprus.svg) |
| `tw` | [Taiwan](https://en.wikipedia.org/wiki/Taiwan) | <img src="circle/other/locales/tw.svg" width="32"> | <img src="square/other/locales/tw.svg" width="32"> | <img src="full-size-simplified/other/locales/tw.svg" height="20"> | [✓](full-size/other/locales/tw.svg) | [<img src="swatches/000094.svg" width="12">`#000094`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_China.svg)<br>[<img src="swatches/FE0000.svg" width="12">`#FE0000`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_China.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_the_Republic_of_China.svg) |
| `xk` | [Kosovo](https://en.wikipedia.org/wiki/Kosovo) | <img src="circle/other/locales/xk.svg" width="32"> | <img src="square/other/locales/xk.svg" width="32"> | <img src="full-size-simplified/other/locales/xk.svg" height="20"> | [✓](full-size/other/locales/xk.svg) | [<img src="swatches/244AA5.svg" width="12">`#244AA5`](https://commons.wikimedia.org/wiki/File:Flag_of_Kosovo.svg)<br>[<img src="swatches/D0A650.svg" width="12">`#D0A650`](https://commons.wikimedia.org/wiki/File:Flag_of_Kosovo.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Kosovo.svg) |

### Organizations & symbols

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `checkered` | [F1 chequered flag](https://en.wikipedia.org/wiki/Racing_flags#Chequered_flag) | <img src="circle/other/orgs/checkered.svg" width="32"> | <img src="square/other/orgs/checkered.svg" width="32"> | <img src="full-size-simplified/other/orgs/checkered.svg" height="20"> | [✓](full-size/other/orgs/checkered.svg) | [<img src="swatches/322C24.svg" width="12">`#322C24`](https://commons.wikimedia.org/wiki/File:F1_chequered_flag.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:F1_chequered_flag.svg) |
| `nato` | [NATO](https://en.wikipedia.org/wiki/NATO) | <img src="circle/other/orgs/nato.svg" width="32"> | <img src="square/other/orgs/nato.svg" width="32"> | <img src="full-size-simplified/other/orgs/nato.svg" height="20"> | [✓](full-size/other/orgs/nato.svg) | [<img src="swatches/004990.svg" width="12">`#004990`](https://en.wikipedia.org/wiki/File:Flag_of_NATO.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_NATO.svg) |
| `olympics` | [Olympics](https://en.wikipedia.org/wiki/Olympic_symbols) | <img src="circle/other/orgs/olympics.svg" width="32"> | <img src="square/other/orgs/olympics.svg" width="32"> | <img src="full-size-simplified/other/orgs/olympics.svg" height="20"> | [✓](full-size/other/orgs/olympics.svg) | [<img src="swatches/0081C8.svg" width="12">`#0081C8`](https://en.wikipedia.org/wiki/File:Olympic_flag.svg)<br>[<img src="swatches/000000.svg" width="12">`#000000`](https://en.wikipedia.org/wiki/File:Olympic_flag.svg)<br>[<img src="swatches/EE334E.svg" width="12">`#EE334E`](https://en.wikipedia.org/wiki/File:Olympic_flag.svg)<br>[<img src="swatches/FCB131.svg" width="12">`#FCB131`](https://en.wikipedia.org/wiki/File:Olympic_flag.svg)<br>[<img src="swatches/00A651.svg" width="12">`#00A651`](https://en.wikipedia.org/wiki/File:Olympic_flag.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Olympic_flag.svg) |
| `un` | [United Nations](https://en.wikipedia.org/wiki/United_Nations) | <img src="circle/other/orgs/un.svg" width="32"> | <img src="square/other/orgs/un.svg" width="32"> | <img src="full-size-simplified/other/orgs/un.svg" height="20"> | [✓](full-size/other/orgs/un.svg) | [<img src="swatches/009EDB.svg" width="12">`#009EDB`](https://en.wikipedia.org/wiki/File:Flag_of_the_United_Nations.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://en.wikipedia.org/wiki/File:Flag_of_the_United_Nations.svg) |

### Subdivisions (ISO 3166-2)

#### Australia

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `au-act` | [Australian Capital Territory](https://en.wikipedia.org/wiki/Australian_Capital_Territory) | | | | | |
| `au-nsw` | [New South Wales](https://en.wikipedia.org/wiki/New_South_Wales) | | | | | |
| `au-nt` | [Northern Territory](https://en.wikipedia.org/wiki/Northern_Territory) | | | | | |
| `au-qld` | [Queensland](https://en.wikipedia.org/wiki/Queensland) | | | | | |
| `au-sa` | [South Australia](https://en.wikipedia.org/wiki/South_Australia) | | | | | |
| `au-tas` | [Tasmania](https://en.wikipedia.org/wiki/Tasmania) | | | | | |
| `au-vic` | [Victoria (state)](https://en.wikipedia.org/wiki/Victoria_(state)) | | | | | |
| `au-wa` | [Western Australia](https://en.wikipedia.org/wiki/Western_Australia) | | | | | |

#### Bonaire, Sint Eustatius and Saba

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `bq-bo` | [Bonaire](https://en.wikipedia.org/wiki/Bonaire) | | | | | |
| `bq-sa` | [Saba](https://en.wikipedia.org/wiki/Saba_(island)) | | | | | |
| `bq-se` | [Sint Eustatius](https://en.wikipedia.org/wiki/Sint_Eustatius) | | | | | |

#### Canada

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `ca-bc` | [British Columbia](https://en.wikipedia.org/wiki/British_Columbia) | <img src="circle/states/ca-bc.svg" width="32"> | <img src="square/states/ca-bc.svg" width="32"> | <img src="full-size-simplified/states/ca-bc.svg" height="20"> | [✓](full-size/states/ca-bc.svg) | [<img src="swatches/0047BB.svg" width="12">`#0047BB`](https://commons.wikimedia.org/wiki/File:Flag_of_British_Columbia.svg)<br>[<img src="swatches/D22630.svg" width="12">`#D22630`](https://commons.wikimedia.org/wiki/File:Flag_of_British_Columbia.svg)<br>[<img src="swatches/FFD200.svg" width="12">`#FFD200`](https://commons.wikimedia.org/wiki/File:Flag_of_British_Columbia.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_British_Columbia.svg) |
| `ca-qc` | [Quebec](https://en.wikipedia.org/wiki/Quebec) | <img src="circle/states/ca-qc.svg" width="32"> | <img src="square/states/ca-qc.svg" width="32"> | <img src="full-size-simplified/states/ca-qc.svg" height="20"> | [✓](full-size/states/ca-qc.svg) | [<img src="swatches/003DA5.svg" width="12">`#003DA5`](https://commons.wikimedia.org/wiki/File:Flag_of_Quebec.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_Quebec.svg) |

#### China

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `cn-xj` | [Xinjiang](https://en.wikipedia.org/wiki/Xinjiang) | | | | | |
| `cn-xz` | [Tibet](https://en.wikipedia.org/wiki/Tibet) | | | | | |

#### Ethiopia

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `et-af` | [Afar Region](https://en.wikipedia.org/wiki/Afar_Region) | | | | | |
| `et-am` | [Amhara Region](https://en.wikipedia.org/wiki/Amhara_Region) | | | | | |
| `et-be` | [Benishangul-Gumuz](https://en.wikipedia.org/wiki/Benishangul-Gumuz_Region) | | | | | |
| `et-ga` | [Gambela](https://en.wikipedia.org/wiki/Gambela_Region) | | | | | |
| `et-ha` | [Harari](https://en.wikipedia.org/wiki/Harari_Region) | | | | | |
| `et-or` | [Oromia](https://en.wikipedia.org/wiki/Oromia_Region) | | | | | |
| `et-si` | [Sidama](https://en.wikipedia.org/wiki/Sidama_Region) | | | | | |
| `et-sn` | [Southern Nations, Nationalities, and Peoples' Region](https://en.wikipedia.org/wiki/Southern_Nations,_Nationalities,_and_Peoples%27_Region) | | | | | |
| `et-so` | [Somali Region](https://en.wikipedia.org/wiki/Somali_Region) | | | | | |
| `et-sw` | [South West Region](https://en.wikipedia.org/wiki/South_West_Ethiopia_Peoples%27_Region) | | | | | |
| `et-ti` | [Tigray](https://en.wikipedia.org/wiki/Tigray_Region) | | | | | |

#### France

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `fr-20r` | [Corsica](https://en.wikipedia.org/wiki/Corsica) | | | | | |
| `fr-bre` | [Brittany](https://en.wikipedia.org/wiki/Brittany) | | | | | |
| `fr-cp` | [Clipperton Island](https://en.wikipedia.org/wiki/Clipperton_Island) | | | | | |

#### Georgia

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `ge-ab` | [Abkhazia](https://en.wikipedia.org/wiki/Abkhazia) | | | | | |

#### Indonesia

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `id-jb` | [West Java](https://en.wikipedia.org/wiki/West_Java) | | | | | |
| `id-jt` | [Central Java](https://en.wikipedia.org/wiki/Central_Java) | | | | | |

#### India

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `in-as` | [Assam](https://en.wikipedia.org/wiki/Assam) | | | | | |
| `in-gj` | [Gujarat](https://en.wikipedia.org/wiki/Gujarat) | | | | | |
| `in-ka` | [Karnataka](https://en.wikipedia.org/wiki/Karnataka) | | | | | |
| `in-mn` | [Manipur](https://en.wikipedia.org/wiki/Manipur) | | | | | |
| `in-mz` | [Mizoram](https://en.wikipedia.org/wiki/Mizoram) | | | | | |
| `in-or` | [Odisha](https://en.wikipedia.org/wiki/Odisha) | | | | | |
| `in-tg` | [Telangana](https://en.wikipedia.org/wiki/Telangana) | | | | | |
| `in-tn` | [Tamil Nadu](https://en.wikipedia.org/wiki/Tamil_Nadu) | | | | | |

#### Iraq

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `iq-kr` | [Kurdistan Region](https://en.wikipedia.org/wiki/Kurdistan_Region) | | | | | |

#### Italy

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `it-21` | [Piedmont](https://en.wikipedia.org/wiki/Piedmont) | | | | | |
| `it-23` | [Aosta Valley](https://en.wikipedia.org/wiki/Aosta_Valley) | | | | | |
| `it-25` | [Lombardy](https://en.wikipedia.org/wiki/Lombardy) | | | | | |
| `it-32` | [Trentino-Alto Adige](https://en.wikipedia.org/wiki/Trentino-Alto_Adige) | | | | | |
| `it-34` | [Veneto](https://en.wikipedia.org/wiki/Veneto) | | | | | |
| `it-36` | [Friuli Venezia Giulia](https://en.wikipedia.org/wiki/Friuli-Venezia_Giulia) | | | | | |
| `it-42` | [Liguria](https://en.wikipedia.org/wiki/Liguria) | | | | | |
| `it-45` | [Emilia-Romagna](https://en.wikipedia.org/wiki/Emilia-Romagna) | | | | | |
| `it-52` | [Tuscany](https://en.wikipedia.org/wiki/Tuscany) | | | | | |
| `it-55` | [Umbria](https://en.wikipedia.org/wiki/Umbria) | | | | | |
| `it-57` | [Marche](https://en.wikipedia.org/wiki/Marche) | | | | | |
| `it-62` | [Lazio](https://en.wikipedia.org/wiki/Lazio) | | | | | |
| `it-65` | [Abruzzo](https://en.wikipedia.org/wiki/Abruzzo) | | | | | |
| `it-67` | [Molise](https://en.wikipedia.org/wiki/Molise) | | | | | |
| `it-72` | [Campania](https://en.wikipedia.org/wiki/Campania) | | | | | |
| `it-75` | [Apulia](https://en.wikipedia.org/wiki/Apulia) | | | | | |
| `it-77` | [Basilicata](https://en.wikipedia.org/wiki/Basilicata) | | | | | |
| `it-78` | [Calabria](https://en.wikipedia.org/wiki/Calabria) | | | | | |
| `it-82` | [Sicily](https://en.wikipedia.org/wiki/Sicily) | | | | | |
| `it-88` | [Sardinia](https://en.wikipedia.org/wiki/Sardinia) | | | | | |

#### Netherlands

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `nl-fr` | [Friesland](https://en.wikipedia.org/wiki/Friesland) | | | | | |

#### Pakistan

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `pk-jk` | [Azad Kashmir](https://en.wikipedia.org/wiki/Azad_Kashmir) | | | | | |
| `pk-sd` | [Sindh](https://en.wikipedia.org/wiki/Sindh) | | | | | |

#### Portugal

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `pt-20` | [Azores](https://en.wikipedia.org/wiki/Azores) | | | | | |
| `pt-30` | [Madeira](https://en.wikipedia.org/wiki/Madeira) | | | | | |

#### Russia

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `ru-ba` | [Bashkortostan](https://en.wikipedia.org/wiki/Bashkortostan) | | | | | |
| `ru-ce` | [Chechnya](https://en.wikipedia.org/wiki/Chechnya) | | | | | |
| `ru-cu` | [Chuvashia](https://en.wikipedia.org/wiki/Chuvashia) | | | | | |
| `ru-da` | [Dagestan](https://en.wikipedia.org/wiki/Dagestan) | | | | | |
| `ru-dpr` | [Donetsk People's Republic](https://en.wikipedia.org/wiki/Donetsk_People%27s_Republic) | | | | | |
| `ru-ko` | [Komi Republic](https://en.wikipedia.org/wiki/Komi_Republic) | | | | | |
| `ru-lpr` | [Luhansk People's Republic](https://en.wikipedia.org/wiki/Luhansk_People%27s_Republic) | | | | | |
| `ru-ta` | [Tatarstan](https://en.wikipedia.org/wiki/Tatarstan) | | | | | |
| `ru-ud` | [Udmurtia](https://en.wikipedia.org/wiki/Udmurtia) | | | | | |

#### Saint Helena, Ascension and Tristan da Cunha

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `sh-ac` | [Ascension Island](https://en.wikipedia.org/wiki/Ascension_Island) | | | | | |
| `sh-hl` | [Saint Helena](https://en.wikipedia.org/wiki/Saint_Helena) | | | | | |
| `sh-ta` | [Tristan da Cunha](https://en.wikipedia.org/wiki/Tristan_da_Cunha) | | | | | |

#### Spain

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `es-ar` | [Aragon](https://en.wikipedia.org/wiki/Aragon) | | | | | |
| `es-ce` | [Ceuta](https://en.wikipedia.org/wiki/Ceuta) | | | | | |
| `es-cn` | [Canary Islands](https://en.wikipedia.org/wiki/Canary_Islands) | | | | | |
| `es-ct` | [Catalonia](https://en.wikipedia.org/wiki/Catalonia) | | | | | |
| `es-ga` | [Galicia](https://en.wikipedia.org/wiki/Galicia_(Spain)) | | | | | |
| `es-ib` | [Balearic Islands](https://en.wikipedia.org/wiki/Balearic_Islands) | | | | | |
| `es-ml` | [Melilla](https://en.wikipedia.org/wiki/Melilla) | | | | | |
| `es-pv` | [Basque Country](https://en.wikipedia.org/wiki/Basque_Country_(autonomous_community)) | | | | | |
| `es-vc` | [Valencia](https://en.wikipedia.org/wiki/Valencian_Community) | | | | | |

#### Switzerland

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `ch-gr` | [Grisons](https://en.wikipedia.org/wiki/Grisons) | | | | | |

#### Ukraine

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `ua-bpr` | [Belgorod People's Republic](https://en.wikipedia.org/wiki/Belgorod_People%27s_Republic) | | | | | |
| `ua-kpr` | [Kursk People's Republic](https://en.wikipedia.org/wiki/Kursk_People%27s_Republic) | | | | | |

#### United Kingdom

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `gb-con` | [Cornwall](https://en.wikipedia.org/wiki/Cornwall) | | | | | |
| `gb-eng` | [England](https://en.wikipedia.org/wiki/England) | | | | | |
| `gb-nir` | [Northern Ireland](https://en.wikipedia.org/wiki/Northern_Ireland) | | | | | |
| `gb-ork` | [Orkney](https://en.wikipedia.org/wiki/Orkney) | | | | | |
| `gb-sct` | [Scotland](https://en.wikipedia.org/wiki/Scotland) | | | | | |
| `gb-wls` | [Wales](https://en.wikipedia.org/wiki/Wales) | | | | | |

#### United States

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `us-ak` | [Alaska](https://en.wikipedia.org/wiki/Alaska) | | | | | |
| `us-al` | [Alabama](https://en.wikipedia.org/wiki/Alabama) | | | | | |
| `us-ar` | [Arkansas](https://en.wikipedia.org/wiki/Arkansas) | | | | | |
| `us-az` | [Arizona](https://en.wikipedia.org/wiki/Arizona) | | | | | |
| `us-ca` | [California](https://en.wikipedia.org/wiki/California) | <img src="circle/states/us-ca.svg" width="32"> | <img src="square/states/us-ca.svg" width="32"> | <img src="full-size-simplified/states/us-ca.svg" height="20"> | [✓](full-size/states/us-ca.svg) | [<img src="swatches/BA0C2F.svg" width="12">`#BA0C2F`](https://commons.wikimedia.org/wiki/File:Flag_of_California.svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Flag_of_California.svg)<br>[<img src="swatches/5C462B.svg" width="12">`#5C462B`](https://commons.wikimedia.org/wiki/File:Flag_of_California.svg)<br>[<img src="swatches/00843D.svg" width="12">`#00843D`](https://commons.wikimedia.org/wiki/File:Flag_of_California.svg)<br>[<img src="swatches/B58150.svg" width="12">`#B58150`](https://commons.wikimedia.org/wiki/File:Flag_of_California.svg) |
| `us-co` | [Colorado](https://en.wikipedia.org/wiki/Colorado) | | | | | |
| `us-dc` | [District of Columbia](https://en.wikipedia.org/wiki/Washington,_D.C.) | | | | | |
| `us-fl` | [Florida](https://en.wikipedia.org/wiki/Florida) | | | | | |
| `us-ga` | [Georgia](https://en.wikipedia.org/wiki/Georgia_(U.S._state)) | | | | | |
| `us-hi` | [Hawaii](https://en.wikipedia.org/wiki/Hawaii) | | | | | |
| `us-in` | [Indiana](https://en.wikipedia.org/wiki/Indiana) | | | | | |
| `us-md` | [Maryland](https://en.wikipedia.org/wiki/Maryland) | | | | | |
| `us-mn` | [Minnesota](https://en.wikipedia.org/wiki/Minnesota) | | | | | |
| `us-mo` | [Missouri](https://en.wikipedia.org/wiki/Missouri) | | | | | |
| `us-ms` | [Mississippi](https://en.wikipedia.org/wiki/Mississippi) | | | | | |
| `us-nc` | [North Carolina](https://en.wikipedia.org/wiki/North_Carolina) | | | | | |
| `us-nm` | [New Mexico](https://en.wikipedia.org/wiki/New_Mexico) | | | | | |
| `us-or` | [Oregon](https://en.wikipedia.org/wiki/Oregon) | | | | | |
| `us-ri` | [Rhode Island](https://en.wikipedia.org/wiki/Rhode_Island) | | | | | |
| `us-sc` | [South Carolina](https://en.wikipedia.org/wiki/South_Carolina) | | | | | |
| `us-tn` | [Tennessee](https://en.wikipedia.org/wiki/Tennessee) | | | | | |
| `us-tx` | [Texas](https://en.wikipedia.org/wiki/Texas) | | | | | |
| `us-wa` | [Washington](https://en.wikipedia.org/wiki/Washington_(state)) | | | | | |
| `us-wi` | [Wisconsin](https://en.wikipedia.org/wiki/Wisconsin) | | | | | |
| `us-wy` | [Wyoming](https://en.wikipedia.org/wiki/Wyoming) | | | | | |

### Historical

| Code | Name | Circle | Square | Simplified | Full-size | Colors |
|------|------|:------:|:----:|:----------:|:---------:|--------|
| `confederacy` | [Confederate battle flag](https://commons.wikimedia.org/wiki/File:Battle_flag_of_the_Confederate_States_of_America_(3-5).svg) | <img src="circle/historical/confederacy.svg" width="32"> | <img src="square/historical/confederacy.svg" width="32"> | <img src="full-size-simplified/historical/confederacy.svg" height="20"> | [✓](full-size/historical/confederacy.svg) | [<img src="swatches/bf0a30.svg" width="12">`#bf0a30`](https://commons.wikimedia.org/wiki/File:Battle_flag_of_the_Confederate_States_of_America_(3-5).svg)<br>[<img src="swatches/FFFFFF.svg" width="12">`#FFFFFF`](https://commons.wikimedia.org/wiki/File:Battle_flag_of_the_Confederate_States_of_America_(3-5).svg)<br>[<img src="swatches/002868.svg" width="12">`#002868`](https://commons.wikimedia.org/wiki/File:Battle_flag_of_the_Confederate_States_of_America_(3-5).svg) |

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
- Official flag colors sourced from [Wikipedia](https://en.wikipedia.org/wiki/Main_Page)/[Wikimedia Commons](https://commons.wikimedia.org/) SVGs (see Colors column in progress tables)

## Usage

### Xcode Asset Catalog

Drag any SVG directly into your asset catalog. Works out of the box — no conversion needed.

### SwiftUI

```swift
Image("us") // after adding to asset catalog
```

### HTML

```html
<img src="svg-flags/square/countries/us.svg" alt="United States" width="30">
```

## License

MIT — see [LICENSE](LICENSE). Based on [circle-flags](https://github.com/HatScripts/circle-flags) by HatScripts.
