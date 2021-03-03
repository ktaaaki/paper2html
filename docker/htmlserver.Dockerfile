FROM alpine:latest

RUN apk update && apk add --no-cache curl unzip libc6-compat \
    && curl -s https://api.github.com/repos/mjpclab/go-http-file-server/releases/latest \
    | grep "browser_download_url.*linux-amd64.zip" | cut -d : -f 2,3 | xargs curl -JLo "ghfs.zip" \
    && unzip "ghfs.zip" \
    && rm "ghfs.zip" \
    && mkdir /paper_cache

CMD [ "./ghfs", "-l", "8080", "-r", "/paper_cache" , "-U", "--global-delete", "--global-archive" ]