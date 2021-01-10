import math
import logging
import os
import shutil
from io import BytesIO
from flask import Flask, request, send_file
import urllib.request
import urllib.parse
from paper2html.paper import Paper
from paper2html.commands import paper2html


app = Flask(__name__)


@app.route('/paper2html')
def render():
    download_url = request.args.get('url')
    app.logger.debug(download_url)
    _, ext = os.path.splitext(download_url)
    if ext != ".pdf":
        return f"{download_url} is not url to pdf."
    cache_dir = "paper_cache"
    if not os.path.exists(cache_dir):
        print('tmp dir does not exists!')
        os.mkdir(cache_dir)
    _, filename = os.path.split(download_url)
    working_dir = os.path.join(cache_dir, urllib.parse.quote(download_url, safe=''))
    pdf_filename = os.path.join(working_dir, filename)
    result_dirname, _ = os.path.splitext(filename)
    result_html = os.path.join(working_dir, result_dirname, f"{result_dirname}_0.html")
    if not os.path.exists(working_dir) or not os.path.exists(result_html):
        print('creating working dir.')
        # generate converted html on server cache
        os.mkdir(working_dir)
        n_div_paragraph = math.inf
        line_margin_rate = None
        verbose = False
        with urllib.request.urlopen(download_url) as uf:
            with open(pdf_filename, 'bw') as of:
                of.write(uf.read())
            print('download pdf.')
            if not os.path.exists(pdf_filename):
                print('download failed.')
        Paper.n_div_paragraph = n_div_paragraph
        for url in paper2html(pdf_filename, working_dir, line_margin_rate, verbose):
            # return send_file(url)
            print('output html file')
            pass
    # delete cache
    with BytesIO() as buffered:
        with open(result_html, 'rb') as f:
            buffered.write(f.read())
        buffered.seek(0)
        shutil.rmtree(working_dir)
        return send_file(buffered, mimetype='text/html')


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # app.run(debug=True, port=8080, host='127.0.0.1')
    app.run(debug=False, port=80, host='0.0.0.0')
