FROM python:latest

RUN apt-get update \
    && apt-get install -y poppler-utils poppler-data \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
    && git clone https://github.com/ktaaaki/paper2html.git \
    && python -m pip --no-cache-dir install -e paper2html
