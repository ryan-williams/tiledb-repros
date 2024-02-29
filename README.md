# flaky tiledbsoma test repro

## Setup
```bash
git clone https://github.com/ryan-williams/tiledbsoma-flaky-test-repro && cd tiledbsoma-flaky-test-repro
pip install click tiledbsoma
```

## Test
```base
# (b)ool (ordered), (B)ool (unordered), 200 reps
./test-categoricals.py -bB -n200
```

## Example
[This GitHub Action][GHA failure] demonstrates a failure (note the [`arm64`] arch, courtesy of `macos-latest-xlarge` runner).

## Help
```bash
test-categoricals.py --help
# Usage: test-categoricals.py [OPTIONS]
#
#   Test reading and writing of categorical columns in a SOMA DataFrame.
#
#   Iff at least 2 pa.dictionary columns are included, ≈5-10% of runs raise
#   `ArrowIndexError` on ARM Macs.
#
# Options:
#   -s, --string-ordered    Include an ordered string column in the pa.schema
#                           and pd.DataFrame
#   -S, --string-unordered  Include an unordered string column in the pa.schema
#                           and pd.DataFrame
#   -i, --int-ordered       Include an ordered int column in the pa.schema and
#                           pd.DataFrame
#   -I, --int-unordered     Include an unordered int column in the pa.schema and
#                           pd.DataFrame
#   -b, --bool-ordered      Include an ordered bool column in the pa.schema and
#                           pd.DataFrame
#   -B, --bool-unordered    Include an unordered bool column in the pa.schema
#                           and pd.DataFrame
#   -n, --num INTEGER       Number of iterations to run
#   -X, --no-short-circuit  Run all -n/--num iterations, even if failures are
#                           encountered (default: short-circuit on first error)
#   -c, --compat-cols       Include "compat" columns (string, int, and bool);
#                           these don't seem to affect anything
#   --help                  Show this message and exit.
```

[GHA failure]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8102533718/job/22145228998#step:8:12
[`arm64`]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8102533718/job/22145228998#step:2:5
