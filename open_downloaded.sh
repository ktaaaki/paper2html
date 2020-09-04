DOWNLOADS_DIR = /home/yourname/Downloads

inotifywait -e create -m ${DOWNLOADS_DIR} --format "%w%f" | \
while read filepath; do
  echo "${filepath}"
  if [ -e "${filepath}" ]; then
    case "${filepath}" in
    *.pdf )
      python -c "from paper2html import open_paper_htmls; open_paper_htmls('${filepath}')"
      ;;
    esac
  fi
done
