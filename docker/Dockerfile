FROM alpine

RUN apk add --no-cache \
        python3-dev \
        py-pip \
        git \
        poppler-utils \
        poppler-data \
        # Cryptography depenencies
        # https://cryptography.io/en/latest/installation.html#alpine
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
        cargo \
        # Pillow depenencies
        # https://pillow.readthedocs.io/en/latest/installation.html#external-libraries
        # https://github.com/python-pillow/docker-images/blob/master/alpine/Dockerfile
        zlib-dev \
        jpeg-dev \
    && git clone https://github.com/ktaaaki/paper2html.git \
    && python3 -m pip --no-cache-dir install -e paper2html

EXPOSE 5000

CMD [ "python3", "/paper2html/paper2html/main.py", "--host=0.0.0.0" ]