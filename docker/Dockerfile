FROM python:slim

LABEL org.opencontainers.image.source=https://github.com/ktaaaki/paper2html

COPY . /paper2html/

RUN apt-get update \
    && apt-get install -y poppler-utils poppler-data \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip --no-cache-dir install -e paper2html

EXPOSE 5000

CMD [ "python", "/paper2html/paper2html/main.py", "--host=0.0.0.0", "--dir=/tmp/paper_cache", "--watch=True" ]