FROM python:slim

LABEL org.opencontainers.image.source=https://github.com/ktaaaki/paper2html

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        poppler-utils \
        poppler-data \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY . /tmp/paper2html/
WORKDIR /tmp
RUN python -m pip --no-cache-dir install -e paper2html

EXPOSE 6003

ENTRYPOINT [ "./paper2html/docker/entrypoint.sh" ]

CMD [ "./paper2html/docker/start.sh" ]
