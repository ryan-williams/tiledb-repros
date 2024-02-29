#!/usr/bin/env python
from os.path import join
from sys import stdout, stderr
from tempfile import TemporaryDirectory

import click
import pandas as pd
import pyarrow as pa

import tiledbsoma as soma
from pyarrow import ArrowIndexError


def err(msg = ''):
    stderr.write(msg + '\n')


@click.command
@click.option('-s', '--string-ordered', is_flag=True, help="Include an ordered string column in the pa.schema and pd.DataFrame")
@click.option('-S', '--string-unordered', is_flag=True, help="Include an unordered string column in the pa.schema and pd.DataFrame")
@click.option('-i', '--int-ordered', is_flag=True, help="Include an ordered int column in the pa.schema and pd.DataFrame")
@click.option('-I', '--int-unordered', is_flag=True, help="Include an unordered int column in the pa.schema and pd.DataFrame")
@click.option('-b', '--bool-ordered', is_flag=True, help="Include an ordered bool column in the pa.schema and pd.DataFrame")
@click.option('-B', '--bool-unordered', is_flag=True, help="Include an unordered bool column in the pa.schema and pd.DataFrame")
@click.option('-n', '--num', type=int, default=200, help="Number of iterations to run")
@click.option('-X', '--no-short-circuit', is_flag=True, help="Run all -n/--num iterations, even if failures are encountered (default: short-circuit on first error)")
@click.option('-c', '--compat-cols', is_flag=True, help='Include "compat" columns (string, int, and bool); these don\'t seem to affect anything')
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
    """Test reading and writing of categorical columns in a SOMA DataFrame.

    Iff at least 2 pa.dictionary columns are included, ≈5-10% of runs raise `ArrowIndexError` on ARM Macs."""
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
    prv_pa0 = None
    prv_pa1 = None
    for i in range(num):
        with TemporaryDirectory() as tmpdir:
            tmp_path = join(tmpdir, 'sdf')
            with soma.DataFrame.create(tmp_path, schema=schema, index_column_names=["soma_joinid"]) as sdf:
                df0 = pd.DataFrame(
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
                pa0 = pa.Table.from_pandas(df0)
                sdf.write(pa0)

            with soma.DataFrame.open(tmp_path) as sdf:
                try:
                    pa1s = list(sdf.read())
                    pa1 = pa.concat_tables(iter(pa1s))
                    df1 = pa1.to_pandas()
                    assert (df0 == df1).all().all()
                    stdout.write('-')
                    stdout.flush()
                except ArrowIndexError as e:
                    err()
                    err("*** Caught ArrowIndexError ***")
                    err(f"Previous iteration: wrote pyarrow Table ({type(prv_pa0)}):")
                    err(f"{prv_pa0}")
                    err()
                    err(f"Previous iteration: read pyarrow Table ({type(prv_pa1)}):")
                    err(f"{prv_pa1}")
                    err()
                    err(f"Current iteration (failing) wrote pyarrow Table ({type(pa0)}):")
                    err(f"{pa0}")
                    err()
                    for pa1t in pa1s:
                        err(f"Current iteration (failing) pyarrow Table ({type(pa1t)}):")
                        err(f"{pa1t}")
                        err()

                    if no_short_circuit:
                        stdout.write('F')
                        stdout.flush()
                    else:
                        stderr.write(f"\nError on attempt {i+1}: {e}\n")
                        raise

            prv_pa0 = pa0
            prv_pa1 = pa1
    print()


if __name__ == "__main__":
    main()
