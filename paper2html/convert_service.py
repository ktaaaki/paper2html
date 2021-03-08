import logging
import math
import os
import shutil
import urllib.request
from io import BytesIO

from flask import Flask, request, send_file
from watchdog.events import PatternMatchingEventHandler, FileSystemEvent
from watchdog.observers import Observer

from paper2html import paper2html
from paper2html.paper import Paper


cache_dir = "paper_cache"


def init_cache_dir():
    if not os.path.exists(cache_dir):
        print('tmp dir does not exists!')
        os.mkdir(cache_dir)
    return cache_dir


def init_temp_dir(download_url, cache_dir):
    _, filename = os.path.split(download_url)
    working_dir = os.path.join(cache_dir, filename)
    if not os.path.exists(working_dir):
        print('creating working dir.')
        os.mkdir(working_dir)
    return working_dir


def get_working_dir(cache_dir, filename):
    basename, _ = os.path.splitext(filename)
    return os.path.join(cache_dir, basename)


class PdfFileEventHandler(PatternMatchingEventHandler):
    def __init__(self, ignore_patterns=None, ignore_directories=True, case_sensitive=False,
                 debug=False, server_mode=False):
        super().__init__(("*.pdf",), ignore_patterns, ignore_directories, case_sensitive)
        self.debug = debug
        self.server_mode = server_mode

    def _is_timing_of_conversion(self, event):
        # file server may write pdf file without locking.
        if self.server_mode and str(event.event_type) != 'closed':
            return False

        if not os.path.exists(event.src_path):
            return False
        base_dir, filename = os.path.split(event.src_path)

        # to ignore intermediate pdf files on some OS (recursive option does not work... ?)
        if not os.path.samefile(base_dir, cache_dir):
            return False

        # already converted
        basename, _ = os.path.splitext(filename)
        if os.path.exists(os.path.join(base_dir, basename)):
            return False

        return True

    def on_any_event(self, event: FileSystemEvent):
        if not self._is_timing_of_conversion(event):
            return

        n_div_paragraph = math.inf
        line_margin_rate = None
        verbose = self.debug
        Paper.n_div_paragraph = n_div_paragraph
        paper2html(event.src_path, cache_dir, line_margin_rate, verbose)

        _, filename = os.path.split(event.src_path)
        stored_pdf_path = os.path.join(get_working_dir(cache_dir, filename), filename)
        shutil.move(event.src_path, stored_pdf_path)


def convert_service_run(host, port, watch, debug):
    app = Flask(__name__)

    def get_pdf_filename(url):
        cache_dir = init_cache_dir()
        temp_dir = init_temp_dir(url, cache_dir)

        _, filename = os.path.split(url)
        pdf_filename = os.path.join(temp_dir, filename)
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

        temp_dir = init_temp_dir(download_url, cache_dir)

        _, filename = os.path.split(download_url)
        basename, _ = os.path.splitext(filename)
        result_html = os.path.join(get_working_dir(cache_dir, filename), f"{basename}_0.html")

        if not os.path.exists(result_html):
            n_div_paragraph = math.inf
            line_margin_rate = None
            verbose = debug
            pdf_filename = get_pdf_filename(download_url)
            download(download_url, pdf_filename)
            if not os.path.exists(pdf_filename):
                return f"please post {pdf_filename} first."
            Paper.n_div_paragraph = n_div_paragraph
            for url in paper2html(pdf_filename, cache_dir, line_margin_rate, verbose):
                # return send_file(url)
                print('output html file')
                pass
            shutil.move(pdf_filename, os.path.join(get_working_dir(cache_dir, filename), filename))
            shutil.rmtree(temp_dir)
        with open(result_html, 'rb') as f:
            buffered = BytesIO(f.read())

        return send_file(buffered, mimetype='text/html')

    @app.errorhandler(500)
    def server_error(e):
        logging.exception('An error occurred during a request.')
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500

    init_cache_dir()
    if watch:
        obs = Observer()
        event_handler = PdfFileEventHandler(
            server_mode=(str(type(obs)) == "<class 'watchdog.observers.inotify.InotifyObserver'>"))
        obs.schedule(event_handler, os.path.abspath(cache_dir), recursive=False)
        obs.start()

    app.run(debug=debug, host=host, port=port)

    if watch:
        obs.unschedule_all()
        obs.stop()
        obs.join()
