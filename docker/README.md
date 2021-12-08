# paper2html server Docker image

## Get container image

Download from GitHub Container Registry.

```shell
$ docker pull ghcr.io/ktaaaki/paper2html:latest
```

Or build by yourself.

```shell
$ git clone https://github.com/ktaaaki/paper2html.git
$ cd ./paper2html
$ docker build . -t paper2html -f ./docker/Dockerfile
```

## Usage

### Conversion PDF on docker host OS to html with paper2html server [experimental]

If you put a PDF file in the `/etc/paper_cache` directory in the container, the conversion will be done automatically.  
So, bind-mount `/etc/paper_cache` on the Docker host and put PDF files there.

```shell
$ mkdir ~/paper_cache
$ cd ~/paper_cache
$ docker run --rm -it -p 6003:6003 -v ${PWD}:/tmp/paper_cache ghcr.io/ktaaaki/paper2html
```

At present it only works on Linux (`ext4` volume).
