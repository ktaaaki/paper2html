DOWNLOADS_DIR = /home/yourname/Downloads

inotifywait -e create -m ${DOWNLOADS_DIR} --format "%f/%e" | \
while read filepath; do
  if [ -e "${filepath}" ]; then
    case "${filepath}" in
    *.pdf )
      python -c "from paper2html import open_paper_htmls; open_paper_htmls('${filepath}')"
      ;;
    esac
  fi
done