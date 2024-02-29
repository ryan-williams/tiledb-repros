#!/usr/bin/env python
from os.path import join
from sys import stdout, stderr
from tempfile import TemporaryDirectory

import click
import pandas as pd
import pyarrow as pa

import tiledbsoma as soma
from pyarrow import ArrowIndexError


@click.command
@click.option('-s', '--string-ordered', is_flag=True)
@click.option('-S', '--string-unordered', is_flag=True)
@click.option('-i', '--int-ordered', is_flag=True)
@click.option('-I', '--int-unordered', is_flag=True)
@click.option('-b', '--bool-ordered', is_flag=True)
@click.option('-B', '--bool-unordered', is_flag=True)
@click.option('-n', '--num', type=int, default=100)
@click.option('-X', '--no-short-circuit', is_flag=True)
@click.option('-c', '--compat-cols', is_flag=True)
def main(
        string_ordered,
        string_unordered,
        int_ordered,
        int_unordered,
        bool_ordered,
        bool_unordered,
        num,
        no_short_circuit,
        compat_cols,
):
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
    for i in range(num):
        with TemporaryDirectory() as tmpdir:
            tmp_path = join(tmpdir, 'sdf')
            with soma.DataFrame.create(tmp_path, schema=schema, index_column_names=["soma_joinid"]) as sdf:
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
                sdf.write(pa.Table.from_pandas(df))

            with soma.DataFrame.open(tmp_path) as sdf:
                try:
                    df2 = sdf.read().concat().to_pandas()
                    assert (df == df2).all().all()
                    stdout.write('-')
                    stdout.flush()
                except ArrowIndexError as e:
                    if no_short_circuit:
                        stdout.write('F')
                        stdout.flush()
                    else:
                        stderr.write(f"\nError on attempt {i+1}: {e}\n")
                        break
    print()


if __name__ == "__main__":
    main()
