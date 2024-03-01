#!/usr/bin/env python
from contextlib import contextmanager
from inspect import getfullargspec
from os import makedirs
from os.path import join, exists
from shutil import rmtree
from sys import stdout, stderr
from tempfile import TemporaryDirectory

import pandas as pd
import pyarrow as pa
import tiledbsoma as soma
from click import option, argument, group, Command
from pyarrow import ArrowIndexError


def err(msg=''):
    stderr.write(msg + '\n')


@group
def cli():
    """Repeatedly write and/or read SOMA DataFrames with configurable categorical columns, to reproduce ArrowIndexErrors."""
    pass


write_opts = [
    option('-s', '--string-ordered', is_flag=True, help="Include an ordered string column in the pa.schema and pd.DataFrame"),
    option('-S', '--string-unordered', is_flag=True, help="Include an unordered string column in the pa.schema and pd.DataFrame"),
    option('-i', '--int-ordered', is_flag=True, help="Include an ordered int column in the pa.schema and pd.DataFrame"),
    option('-I', '--int-unordered', is_flag=True, help="Include an unordered int column in the pa.schema and pd.DataFrame"),
    option('-b', '--bool-ordered', is_flag=True, help="Include an ordered bool column in the pa.schema and pd.DataFrame"),
    option('-B', '--bool-unordered', is_flag=True, help="Include an unordered bool column in the pa.schema and pd.DataFrame"),
    option('-c', '--compat-cols', is_flag=True, help='Include "compat" columns (string, int, and bool); these don\'t seem to affect anything'),
]


def opts(_opts):
    def wrapper(fn):
        _fn = fn
        for opt in _opts:
            fn = opt(fn)
        return fn
    return wrapper


@cli.command("write")
@opts(write_opts)
@argument('path')
def write(
        string_ordered,
        string_unordered,
        int_ordered,
        int_unordered,
        bool_ordered,
        bool_unordered,
        compat_cols,
        path,
):
    """Test writing a SOMA DataFrame

    Iff at least 2 pa.dictionary columns are included, ≈5-10% of written datasets raise `ArrowIndexError` on read, on ARM Macs.
    """
    include_fields = {
        "soma_joinid": True,
        "string-ordered": string_ordered,
        "string-unordered": string_unordered,
        "int-ordered": int_ordered,
        "int-unordered": int_unordered,
        "bool-ordered": bool_ordered,
        "bool-unordered": bool_unordered,
        "string-compat": compat_cols,
        "int-compat": compat_cols,
        "bool-compat": compat_cols,
    }
    schema = pa.schema(
        [
            (k, v)
            for k, v in [
            ("soma_joinid", pa.int64()),
            ("string-ordered", pa.dictionary(pa.int8(), pa.large_string(), ordered=True)),
            ("string-unordered", pa.dictionary(pa.int8(), pa.large_string())),
            ("string-compat", pa.large_string()),
            ("int-ordered", pa.dictionary(pa.int8(), pa.int64(), ordered=True)),
            ("int-unordered", pa.dictionary(pa.int8(), pa.int64())),
            ("int-compat", pa.int64()),
            ("bool-ordered", pa.dictionary(pa.int8(), pa.bool_(), ordered=True)),
            ("bool-unordered", pa.dictionary(pa.int8(), pa.bool_())),
            ("bool-compat", pa.bool_()),
        ]
            if include_fields[k]
        ]
    )
    with soma.DataFrame.create(path, schema=schema, index_column_names=["soma_joinid"]) as sdf:
        df = pd.DataFrame(
            data={
                k: v
                for k, v in {
                    "soma_joinid": [0, 1, 2, 3],
                    "string-ordered": pd.Categorical(["a", "b", "a", "b"], ordered=True, categories=["b", "a"]),
                    "string-unordered": pd.Categorical(["a", "b", "a", "b"], ordered=False, categories=["b", "a"]),
                    "string-compat": pd.Categorical(["a", "b", "a", "b"], ordered=False, categories=["a", "b"]),
                    "int-ordered": pd.Categorical([777777777, 888888888, 777777777, 888888888], ordered=True, categories=[888888888, 777777777]),
                    "int-unordered": pd.Categorical([777777777, 888888888, 777777777, 888888888], ordered=False, categories=[888888888, 777777777]),
                    "int-compat": pd.Categorical([777777777, 888888888, 777777777, 888888888], ordered=False, categories=[777777777, 888888888]),
                    "bool-ordered": pd.Categorical( [True, False, True, False], ordered=True, categories=[True, False]),
                    "bool-unordered": pd.Categorical([True, False, True, False], ordered=False, categories=[True, False]),
                    "bool-compat": pd.Categorical([True, False, True, False], ordered=False, categories=[True, False]),
                }.items()
                if include_fields[k]
            }
        )
        tbl = pa.Table.from_pandas(df)
        sdf.write(tbl)
        err(f"Wrote pyarrow Table {tbl}")
        err()


@cli.command("read")
@argument('path')
def read(path):
    """Test reading a SOMA DataFrame written by `test-categoricals.py write …`."""
    with soma.DataFrame.open(path) as sdf:
        pa1 = pa.concat_tables(sdf.read())
        try:
            pa1.to_pandas()
            err(f"Read pyarrow table + called to_pandas():")
            err(f"{pa1}")
            err()
        except ArrowIndexError:
            err(f"Failed to convert pyarrow Table to_pandas():")
            err(f"{pa1}")
            err()
            raise


@contextmanager
def dir_context(path: str, rm: bool = False, mkdir: bool = True):
    if path is None:
        with TemporaryDirectory() as tmpdir:
            yield tmpdir
    else:
        if exists(path) and rm:
            rmtree(path)
        if mkdir:
            makedirs(path, exist_ok=True)
        yield path


def call(fn, kwargs0, **kwargs1):
    if isinstance(fn, Command):
        fn = fn.callback
    spec = getfullargspec(fn)
    return fn(
        **{
            k: v
            for k, v in kwargs0.items()
            if k in spec.args and k not in kwargs1
        },
        **kwargs1
    )


@cli.command("both")
@opts(write_opts)
@option('-n', '--num', type=int, default=500, help="Number of iterations to run")
@option('-O', '--no-overwrite', is_flag=True, help="Don't remove+overwrite existing out-dir")
@option('-X', '--no-short-circuit', is_flag=True, help="Run all -n/--num iterations, even if failures are encountered (default: short-circuit on first error)")
@argument('out-dir', required=False)
def both(num, no_overwrite, no_short_circuit, out_dir, **kwargs):
    """Repeatedly round-trip write+read SOMA DataFrames, to test for ArrowIndexErrors.

    When an `out-dir` argument is provided, each iteration's dataset is preserved there when execution completes,
    otherwise they are written to a temporary directory.

    Short-circuits on first error by default; override with -X/--no-short-circuit."""
    numlen = len(str(num - 1))
    if out_dir and exists(out_dir) and not no_overwrite:
        rmtree(out_dir)
    for i in range(num):
        with dir_context(out_dir) as _out_dir:
            out_path = join(_out_dir, f"test{i:0{numlen}d}.soma")
            call(write, kwargs, path=out_path)
            try:
                call(read, kwargs, path=out_path)
            except ArrowIndexError as e:
                if not no_short_circuit:
                    stderr.write(f"\nError on attempt {i+1}: {e}\n")
                    raise


if __name__ == "__main__":
    cli()
