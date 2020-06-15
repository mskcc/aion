FROM continuumio/miniconda3:4.5.4

ARG COMMIT_VERSION="master"

ENV VERSION ${COMMIT_VERSION}

RUN conda install pandas \
    && git clone https://github.com/mskcc/aion /usr/bin/aion \
    && cd /usr/bin/aion \
    && git checkout $VERSION

RUN pip install ruamel.yaml requests
