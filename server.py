import math
import os
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
        os.mkdir(cache_dir)
    _, filename = os.path.split(download_url)
    working_dir = os.path.join(cache_dir, urllib.parse.quote(download_url, safe=''))
    pdf_filename = os.path.join(working_dir, filename)
    if not os.path.exists(working_dir):
        # generate converted html on server cache
        os.mkdir(working_dir)
        n_div_paragraph = math.inf
        line_margin_rate = None
        verbose = False
        with urllib.request.urlopen(download_url) as uf:
            with open(pdf_filename, 'bw') as of:
                of.write(uf.read())
        Paper.n_div_paragraph = n_div_paragraph
        for url in paper2html(pdf_filename, working_dir, line_margin_rate, verbose):
            # return send_file(url)
            pass
    result_dirname, _ = os.path.splitext(filename)
    result_html = os.path.join(working_dir, result_dirname, f"{result_dirname}_0.html")
    return send_file(result_html)


# TODO: リクエストがidでない，/paper2html/http:../../resources/<path>がいい
@app.route('/resources/<path>')
def get_resources(path):
    local_path = f"templates/resources/{path}"
    return send_file(local_path)


@app.route('/resources/original_images/<path>')
def get_resources2(path):
    local_path = f"templates/resources/original_images/{path}"
    return send_file(local_path)


@app.route('/resources/crops/<path>')
def get_resources3(path):
    local_path = f"templates/resources/crops/{path}"
    return send_file(local_path)


if __name__ == '__main__':
    app.run(debug=True)
