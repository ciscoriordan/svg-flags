// Runs svgo over a batch of files in one Node process, which is much faster
// than one npx call per file. Reads a JSON job list from stdin:
//   [{"in": "a.svg", "out": "b.svg", "pass": "first" | "final", "precision": 2}]
//
// "first" inlines CSS and turns style attributes into presentation
// attributes, so the Python cleaner can work on plain attributes. It keeps
// every path vertex: the cleaner draws markers at the vertices afterwards,
// and svgo would otherwise drop zero-length segments such as "h0" and
// closing segments that return to the start, whose vertices carry markers
// (it only protects marker paths from collapsing repeated commands). "final"
// compacts the cleaned file. Both never shorten colors, because the repo
// stores colors as uppercase 6-digit hex. (svgo 4 keeps the viewBox by
// default.)
import { readFileSync, writeFileSync } from "node:fs";
import { optimize } from "svgo";

const keepColors = { names2hex: true, rgb2hex: true, shorthex: false, shortname: false, currentColor: false };

function config(pass, precision) {
  const overrides = {
    convertColors: keepColors,
    inlineStyles: { onlyMatchedOnce: false },
    convertPathData: { floatPrecision: precision },
    cleanupNumericValues: { floatPrecision: precision },
    // Matrix entries are rounded by decimals, not significant digits; some
    // Commons files scale coordinates in the millions by 1e-6, which would
    // round to zero and erase the artwork.
    convertTransform: { floatPrecision: precision + 1, transformPrecision: 12, degPrecision: 6 },
  };
  if (pass === "first") {
    overrides.convertPathData = { ...overrides.convertPathData, removeUseless: false, convertToZ: false };
  }
  if (pass === "final") {
    // Ids were already namespaced by the cleaner; renaming them would undo
    // the guarantee that they cannot collide with the circle/square clip ids.
    overrides.cleanupIds = false;
  }
  return {
    multipass: true,
    floatPrecision: precision,
    plugins: [{ name: "preset-default", params: { overrides } }, "convertStyleToAttrs"],
  };
}

const jobs = JSON.parse(readFileSync(0, "utf8"));
let failed = 0;
for (const job of jobs) {
  try {
    const result = optimize(readFileSync(job.in, "utf8"), { path: job.in, ...config(job.pass, job.precision) });
    writeFileSync(job.out, result.data);
  } catch (error) {
    failed += 1;
    console.error(`${job.in}: ${error.message}`);
  }
}
process.exit(failed ? 1 : 0);
