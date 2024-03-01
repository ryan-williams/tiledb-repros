FROM ubuntu:22.04
RUN apt-get update -y \
 && apt-get install -y build-essential cmake git \
 && apt-get install -y python3 python3-pip python-is-python3 python-dev-is-python3

WORKDIR src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

ENTRYPOINT [ "./test-categoricals.py" ]
CMD [ "read", "nok.soma" ]
