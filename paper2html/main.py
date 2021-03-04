import math
import logging
import os
import shutil
import argparse
from io import BytesIO
from flask import Flask, request, send_file
import urllib.request
import urllib.parse
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from paper2html.paper import Paper
from paper2html.commands import paper2html


cache_dir = "paper_cache"


def init_cache_dir():
    if not os.path.exists(cache_dir):
        print('tmp dir does not exists!')
        os.mkdir(cache_dir)
    return cache_dir


def init_working_dir(download_url, cache_dir):
    _, filename = os.path.split(download_url)
    working_dir = os.path.join(cache_dir, urllib.parse.quote(download_url, safe=''))
    if not os.path.exists(working_dir):
        print('creating working dir.')
        os.mkdir(working_dir)
    return working_dir


class PdfFileEventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns=("*.pdf",), ignore_patterns=None, ignore_directories=True, case_sensitive=False,
                 debug=False):
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.debug = debug

    def on_any_event(self, event):
        if not os.path.exists(event.src_path):
            return

        n_div_paragraph = math.inf
        line_margin_rate = None
        verbose = self.debug
        Paper.n_div_paragraph = n_div_paragraph
        paper2html(event.src_path, cache_dir, line_margin_rate, verbose)


class ConvertService:
    @classmethod
    def run(cls, debug, host, port):
        app = Flask(__name__)

        def get_pdf_filename(url):
            cache_dir = init_cache_dir()
            working_dir = init_working_dir(url, cache_dir)

            _, filename = os.path.split(url)
            pdf_filename = os.path.join(working_dir, filename)
            return pdf_filename

        def download(url, filename):
            with urllib.request.urlopen(url) as uf:
                with open(filename, 'bw') as of:
                    of.write(uf.read())
                print('download pdf.')
                if not os.path.exists(filename):
                    print('download failed.')

        @app.route('/paper2html')
        def render():
            download_url = request.args.get('url')
            app.logger.debug(download_url)
            _, ext = os.path.splitext(download_url)
            if ext != ".pdf":
                return f"{download_url} is not url to pdf."

            working_dir = init_working_dir(download_url, cache_dir)

            _, filename = os.path.split(download_url)
            result_dirname, _ = os.path.splitext(filename)
            result_html = os.path.join(working_dir, result_dirname, f"{result_dirname}_0.html")

            if not os.path.exists(result_html):
                n_div_paragraph = math.inf
                line_margin_rate = None
                verbose = debug
                pdf_filename = get_pdf_filename(download_url)
                download(download_url, pdf_filename)
                if not os.path.exists(pdf_filename):
                    return f"please post {pdf_filename} first."
                Paper.n_div_paragraph = n_div_paragraph
                for url in paper2html(pdf_filename, working_dir, line_margin_rate, verbose):
                    # return send_file(url)
                    print('output html file')
                    pass
            with open(result_html, 'rb') as f:
                buffered = BytesIO(f.read())
                if debug:
                    shutil.rmtree(working_dir)
            return send_file(buffered, mimetype='text/html')

        @app.errorhandler(500)
        def server_error(e):
            logging.exception('An error occurred during a request.')
            return """
            An internal error occurred: <pre>{}</pre>
            See logs for full stacktrace.
            """.format(e), 500

        app.run(debug=debug, host=host, port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=bool, default=False)
    parser.add_argument("--host", type=str, default="127.0.0.1", help="use 0.0.0.0 if you use it on a server.")
    parser.add_argument("--port", type=int, default=5000, help="use 80 if you use it on a server.")
    parser.add_argument("--watch", type=bool, default=False,
                        help="automatically convert local PDFs on the paper_cache directory.")
    args = parser.parse_args()

    init_cache_dir()
    if args.watch:
        event_handler = PdfFileEventHandler()
        obs = Observer()
        obs.schedule(event_handler, os.path.abspath(cache_dir), recursive=False)
        obs.start()

    ConvertService.run(debug=args.debug, host=args.host, port=args.port)

    if args.watch:
        obs.unschedule_all()
        obs.stop()
        obs.join()
