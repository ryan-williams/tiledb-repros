# flaky tiledbsoma test repro
ARM Macs write invalid SOMA archives ≈10% of the time, iff at least 2 `pa.dictionary` columns are included.

- This issue is believed to be fixed, as of [TileDB-SOMA#2194](https://github.com/single-cell-data/TileDB-SOMA/pull/2194).
- TileDB-SOMA was unnecessarily evolving a schema for each column, which could potentially result in multiple evolutions at the same millisecond, which is known to cause issues.

## Repro

### Clone + install
```bash
git clone https://github.com/ryan-williams/tiledbsoma-flaky-test-repro && cd tiledbsoma-flaky-test-repro
pip install click tiledbsoma
```

### Reads fail on [`nok.soma`] example (any OS)
```bash
./test-categoricals.py read nok.soma
# Failed to convert pyarrow Table to_pandas():
# pyarrow.Table
# soma_joinid: int64
# bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
# bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
# ----
# soma_joinid: [[0,1,2,3]]
# bool-ordered: [  -- dictionary:
# [true,false]  -- indices:
# [0,1,0,1]]
# bool-unordered: [  -- dictionary:
# []  -- indices:
# [0,1,0,1]]
#
# Traceback (most recent call last):
#   File "./test-categoricals.py", line 198, in <module>
#     cli()
#   File "$PYTHON/site-packages/click/core.py", line 1157, in __call__
#     return self.main(*args, **kwargs)
#   File "$PYTHON/site-packages/click/core.py", line 1078, in main
#     rv = self.invoke(ctx)
#   File "$PYTHON/site-packages/click/core.py", line 1688, in invoke
#     return _process_result(sub_ctx.command.invoke(sub_ctx))
#   File "$PYTHON/site-packages/click/core.py", line 1434, in invoke
#     return ctx.invoke(self.callback, **ctx.params)
#   File "$PYTHON/site-packages/click/core.py", line 783, in invoke
#     return __callback(*args, **kwargs)
#   File "./test-categoricals.py", line 124, in read
#     pa1.to_pandas()
#   File "pyarrow/array.pxi", line 837, in pyarrow.lib._PandasConvertible.to_pandas
#   File "pyarrow/table.pxi", line 4114, in pyarrow.lib.Table._to_pandas
#   File "$PYTHON/site-packages/pyarrow/pandas_compat.py", line 820, in table_to_blockmanager
#     blocks = _table_to_blocks(options, table, categories, ext_columns_dtypes)
#   File "$PYTHON/site-packages/pyarrow/pandas_compat.py", line 1168, in _table_to_blocks
#     result = pa.lib.table_to_blocks(options, block_table, categories,
#   File "pyarrow/table.pxi", line 2771, in pyarrow.lib.table_to_blocks
#   File "pyarrow/error.pxi", line 127, in pyarrow.lib.check_status
# pyarrow.lib.ArrowIndexError: Index 0 out of bounds
```

([GitHub Actions example][GHA nok])

Note the empty `dictionaries:\n[]` in the `bool-unordered` output; the array should be `[true,false]`, as it is when reading a valid SOMA archive:

### Reads succeed on [`ok.soma`] example (any OS)
```bash
./test-categoricals.py read ok.soma
# Read pyarrow table + called to_pandas():
# pyarrow.Table
# soma_joinid: int64
# bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
# bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
# ----
# soma_joinid: [[0,1,2,3]]
# bool-ordered: [  -- dictionary:
# [true,false]  -- indices:
# [0,1,0,1]]
# bool-unordered: [  -- dictionary:
# [true,false]  -- indices:
# [0,1,0,1]]
```

([GitHub Actions example][GHA ok])

### Generate an invalid SOMA archive (ARM Macs only)
```bash
# (b)ool (ordered), (B)ool (unordered), 500 reps
./test-categoricals.py both -bB -n500 out
```

You should see a bunch of `Wrote pyarrow Table` / `Read pyarrow Table` blocks, and then a `Failed to convert` block, like in the `nok.soma` example above.

<details><summary>Full example output</summary>

```
Wrote pyarrow Table pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Read pyarrow table + called to_pandas():
pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Wrote pyarrow Table pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Read pyarrow table + called to_pandas():
pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Wrote pyarrow Table pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Read pyarrow table + called to_pandas():
pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Wrote pyarrow Table pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]

Failed to convert pyarrow Table to_pandas():
pyarrow.Table
soma_joinid: int64
bool-ordered: dictionary<values=bool, indices=int8, ordered=1>
bool-unordered: dictionary<values=bool, indices=int8, ordered=0>
----
soma_joinid: [[0,1,2,3]]
bool-ordered: [  -- dictionary:
[true,false]  -- indices:
[0,1,0,1]]
bool-unordered: [  -- dictionary:
[]  -- indices:
[0,1,0,1]]


Error on attempt 4: Index 0 out of bounds
Traceback (most recent call last):
  File "./test-categoricals.py", line 192, in <module>
    cli()
  File "$PYTHON/site-packages/click/core.py", line 1157, in __call__
    return self.main(*args, **kwargs)
  File "$PYTHON/site-packages/click/core.py", line 1078, in main
    rv = self.invoke(ctx)
  File "$PYTHON/site-packages/click/core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
  File "$PYTHON/site-packages/click/core.py", line 1434, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "$PYTHON/site-packages/click/core.py", line 783, in invoke
    return __callback(*args, **kwargs)
  File "./test-categoricals.py", line 184, in both
    call(read, kwargs, path=out_path)
  File "./test-categoricals.py", line 153, in call
    return fn(
  File "./test-categoricals.py", line 125, in read
    pa1.to_pandas()
  File "pyarrow/array.pxi", line 837, in pyarrow.lib._PandasConvertible.to_pandas
  File "pyarrow/table.pxi", line 4114, in pyarrow.lib.Table._to_pandas
  File "$PYTHON/site-packages/pyarrow/pandas_compat.py", line 820, in table_to_blockmanager
    blocks = _table_to_blocks(options, table, categories, ext_columns_dtypes)
  File "$PYTHON/site-packages/pyarrow/pandas_compat.py", line 1168, in _table_to_blocks
    result = pa.lib.table_to_blocks(options, block_table, categories,
  File "pyarrow/table.pxi", line 2771, in pyarrow.lib.table_to_blocks
  File "pyarrow/error.pxi", line 127, in pyarrow.lib.check_status
pyarrow.lib.ArrowIndexError: Index 0 out of bounds
```
</details>

The `out/` dir will look like:
```bash
tree -L 1 out
# out
# ├── test000.soma
# ├── test001.soma
# ├── test002.soma
# └── test003.soma
```

The last entry will be the one that failed, and the others will have succeeded. [`ok.soma`] and [`nok.soma`] were copied from such a run:

```bash
cp -r `ls out | tail -1` nok.soma
cp -r `ls out | tail -2 | head -1` ok.soma
```

[Here's a GitHub Actions example][GHA write fail].

## Help
```bash
./test-categoricals.py --help
# Usage: test-categoricals.py [OPTIONS] COMMAND [ARGS]...
#
#   Repeatedly write and/or read SOMA DataFrames with configurable categorical
#   columns, to reproduce ArrowIndexErrors.
#
# Options:
#   --help  Show this message and exit.
#
# Commands:
#   both   Repeatedly round-trip write+read SOMA DataFrames, to test for...
#   read   Test reading a SOMA DataFrame written by `test-categoricals.py...
#   write  Test writing a SOMA DataFrame
```

[GHA failure]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8102760527/job/22145939851#step:8:41
[`arm64`]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8102760527/job/22145939851#step:2:5
[GHA nok]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8114003712/job/22178645697#step:9:1
[GHA ok]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8114003712/job/22178645697#step:8:1
[GHA write fail]: https://github.com/ryan-williams/tiledbsoma-flaky-test-repro/actions/runs/8114425951/job/22180026437#step:8:385
[`ok.soma`]: ./ok.soma
[`nok.soma`]: ./nok.soma
