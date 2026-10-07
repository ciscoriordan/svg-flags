"""Regression checks for standalone assets (run with unittest discover)."""
from pathlib import Path
import json
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = ('circle', 'square', 'full-size', 'full-size-simplified')


class SVGAssetsTests(unittest.TestCase):
    def test_references_resolve_uniquely(self):
        for variant in VARIANTS:
            for path in (ROOT / variant).rglob('*.svg'):
                with self.subTest(path=path.relative_to(ROOT)):
                    root = ET.parse(path).getroot()
                    ids = [e.attrib['id'] for e in root.iter() if 'id' in e.attrib]
                    self.assertEqual(len(ids), len(set(ids)))
                    for element in root.iter():
                        for value in element.attrib.values():
                            for ref in re.findall(r'url\(#([^)]*)\)', value):
                                self.assertIn(ref, ids)

    def test_unsupported_svg_elements_are_absent(self):
        forbidden = {'mask', 'use', 'text', 'filter', 'marker', 'image', 'style'}
        for variant in VARIANTS:
            for path in (ROOT / variant).rglob('*.svg'):
                with self.subTest(path=path.relative_to(ROOT)):
                    tags = {e.tag.rsplit('}', 1)[-1] for e in ET.parse(path).iter()}
                    self.assertFalse(tags & forbidden, tags & forbidden)

    def test_israel_has_scalable_viewbox(self):
        for variant in VARIANTS[2:]:
            country = ROOT / variant / 'countries/il.svg'
            self.assertEqual(ET.parse(country).getroot().get('viewBox'), '0 0 1100 800')
            self.assertEqual(country.read_bytes(), (ROOT / variant / 'languages/he.svg').read_bytes())

    def test_israel_triangles_point_in_opposite_directions(self):
        # Both triangles formerly pointed upward. The lower triangle must have
        # a broad top edge and its apex below the flag's vertical midpoint.
        for variant in VARIANTS[2:]:
            for name in ('countries/il', 'languages/he'):
                root = ET.parse(ROOT / variant / (name + '.svg')).getroot()
                triangles = [e for e in root if e.get('stroke') == '#0038B8']
                self.assertEqual(len(triangles), 2)
                self.assertIn('L550.00001 254.29492', triangles[0].get('d'))
                self.assertIn('L550 545.70508', triangles[1].get('d'))

    def test_regional_languages_have_every_variant(self):
        for code in ('en-ca', 'en-us', 'es-mx', 'es-us', 'fr-ca', 'fr-ca-qc'):
            for variant in VARIANTS:
                path = ROOT / variant / 'languages' / f'{code}.svg'
                self.assertTrue(path.exists(), path)
                if variant.startswith('full-size'):
                    self.assertEqual(ET.parse(path).getroot().get('viewBox'), '0 0 900 600')

    def test_restored_subdivisions_keep_source_proportions(self):
        recipes = json.loads((ROOT / 'scripts/subdivisions/flags.json').read_text())['flags']
        sources = json.loads((ROOT / 'scripts/subdivisions/sources.json').read_text())
        for code, recipe in recipes.items():
            if not recipe.get('full_size_only'):
                continue
            with self.subTest(code=code):
                full = ROOT / 'full-size/states' / (code + '.svg')
                root = ET.parse(full).getroot()
                viewbox = [float(x) for x in root.get('viewBox').split()]
                source = sources[code]['revision']
                self.assertAlmostEqual(viewbox[2] / viewbox[3], source['width'] / source['height'], delta=0.005)
                self.assertNotEqual(full.read_bytes(), (ROOT / 'square/states' / (code + '.svg')).read_bytes())
                self.assertEqual(full.read_bytes(), (ROOT / 'full-size-simplified/states' / (code + '.svg')).read_bytes())

    def test_mexico_has_standard_border(self):
        self.assertIn('<!-- border --><circle cx="256" cy="256" r="256" fill="none" stroke="#cdcfd3" stroke-width="16"/>',
                      (ROOT / 'circle/countries/mx.svg').read_text())


if __name__ == '__main__':
    unittest.main()
