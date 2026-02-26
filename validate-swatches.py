#!/usr/bin/env python3
"""Validate that README swatch colors match the actual SVG colors for each flag."""

import re
import os
import sys


def validate_swatches():
    readme = open("README.md").read()
    broken = []

    for line in readme.split("\n"):
        m = re.match(
            r"\|\s*(\w{2})\s*\|.*circle/countries/\1\.svg.*\|([^|]*)\|?\s*$", line
        )
        if not m:
            continue
        code = m.group(1)
        swatch_section = m.group(2)

        readme_colors = set(
            c.upper()
            for c in re.findall(r"swatches/([0-9A-Fa-f]{6})\.svg", swatch_section)
        )

        circle_path = f"circle/countries/{code}.svg"
        if not os.path.exists(circle_path):
            continue
        circle_content = open(circle_path).read()

        svg_colors = set()
        for c in re.findall(
            r'(?:fill|stroke)="#([0-9A-Fa-f]{3,6})"', circle_content
        ):
            if len(c) == 3:
                c = c[0] * 2 + c[1] * 2 + c[2] * 2
            c = c.upper()
            if c == "CDCFD3":
                continue
            svg_colors.add(c)

        missing_from_readme = svg_colors - readme_colors
        extra_in_readme = readme_colors - svg_colors

        if missing_from_readme or extra_in_readme:
            parts = [f"  {code}:"]
            if missing_from_readme:
                parts.append(
                    f"    SVG has {sorted(missing_from_readme)} not in README"
                )
            if extra_in_readme:
                parts.append(
                    f"    README has {sorted(extra_in_readme)} not in SVG"
                )
            broken.append("\n".join(parts))

    if broken:
        print(f"Found {len(broken)} mismatches:\n")
        print("\n".join(broken))
        return 1
    else:
        print("All swatches match!")
        return 0


if __name__ == "__main__":
    sys.exit(validate_swatches())
