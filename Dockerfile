FROM ubuntu:22.04
RUN apt-get update -y \
 && apt-get install -y build-essential cmake git \
 && apt-get install -y python3 python3-pip python-is-python3 python-dev-is-python3

RUN git clone https://github.com/single-cell-data/TileDB-SOMA
WORKDIR TileDB-SOMA

ARG ref=main
RUN git checkout $ref
RUN make install
RUN pip install -r apis/python/requirements_dev.txt  # required for pytest (only in some commits, back in time?)
RUN pytest apis/python/tests/test_dataframe.py::test_write_categorical_types
