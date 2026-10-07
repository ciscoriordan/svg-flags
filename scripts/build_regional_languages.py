#!/usr/bin/env python3
"""Build 3:2 regional language composites, region upper-left/language lower-right.

Use each variant's own country artwork, centered and uniformly scaled to cover
its half, preserving emblems' proportions. Run from any directory.
"""
from copy import deepcopy
from pathlib import Path
import sys
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent / 'subdivisions'))
import svgtools as st
from clean import establish_size

ROOT = Path(__file__).resolve().parent.parent
PAIRS = {
    'en-ca': ('countries/ca', 'countries/gb'),
    'en-us': ('countries/us', 'countries/gb'),
    'es-mx': ('countries/mx', 'countries/es'),
    'es-us': ('countries/us', 'countries/es'),
    'fr-ca': ('countries/ca', 'countries/fr'),
    'fr-ca-qc': ('states/ca-qc', 'countries/fr'),
}


def build(variant, code, pair):
    root = etree.Element(st.svg_tag('svg'), nsmap={None: st.SVG_NS},
                         width='900', height='600', viewBox='0 0 900 600')
    defs = etree.SubElement(root, st.svg_tag('defs'))
    for i, (source, points) in enumerate(zip(pair, ('0,0 900,0 0,600', '900,0 900,600 0,600'))):
        clip_id = f'{code}-half-{i}'
        clip = etree.SubElement(defs, st.svg_tag('clipPath'), id=clip_id)
        etree.SubElement(clip, st.svg_tag('polygon'), points=points)
        art = etree.parse(str(ROOT / variant / (source + '.svg'))).getroot()
        _, _, (x, y, w, h) = establish_size(art, {})
        st.prefix_ids(art, f'{code}-{i}')
        scale = max(900 / w, 600 / h)
        outer = etree.SubElement(root, st.svg_tag('g'), {'clip-path': f'url(#{clip_id})'})
        group = etree.SubElement(outer, st.svg_tag('g'),
            transform=f'translate({450 - (x + w / 2) * scale:g} {300 - (y + h / 2) * scale:g}) scale({scale:g})')
        for key, value in art.attrib.items():
            if key in st.PRESENTATION_ATTRS:
                group.set(key, value)
        group.extend(deepcopy(list(art)))
    st.normalize_colors(root)
    etree.cleanup_namespaces(root)
    (ROOT / variant / 'languages' / f'{code}.svg').write_bytes(etree.tostring(root) + b'\n')


if __name__ == '__main__':
    for variant in ('full-size', 'full-size-simplified'):
        for code, pair in PAIRS.items():
            build(variant, code, pair)
