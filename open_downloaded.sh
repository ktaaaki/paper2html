DOWNLOADS_DIR=${HOME}/Downloads
BROWSER_PATH=/usr/bin/google-chrome

inotifywait -e create -m ${DOWNLOADS_DIR} --format "%w%f" | \
while read filepath; do
  echo "${filepath}"
  if [ -e "${filepath}" ]; then
    case "${filepath}" in
    *.pdf )
      python -c "from paper2html import open_paper_htmls; open_paper_htmls('${filepath}', browser_path='${BROWSER_PATH}')"
      ;;
    esac
  fi
done
