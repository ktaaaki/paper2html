import logging
import math
import os
import shutil
import urllib.request

from flask import Flask, request, send_file
from watchdog.events import PatternMatchingEventHandler, FileSystemEvent
from watchdog.observers import Observer

from paper2html import paper2html
from paper2html.paper import Paper


def init_cache_dir():
    cache_dir = "paper_cache"
    if not os.path.exists(cache_dir):
        print('tmp dir does not exists!')
        os.mkdir(cache_dir)
    return cache_dir


def init_working_dir(cache_dir, filename):
    basename, _ = os.path.splitext(filename)
    working_dir = os.path.join(cache_dir, basename)
    if not os.path.exists(working_dir):
        print('creating working dir.')
        os.mkdir(working_dir)
    return working_dir


def paper2one_html(src_path, cache_dir, debug):
    line_margin_rate = None
    verbose = debug
    Paper.n_div_paragraph = math.inf
    results = list(paper2html(src_path, cache_dir, line_margin_rate, verbose))
    assert len(results) == 1
    return results[0]


def download(url, dir_path):
    _, filename = os.path.split(url)
    file_path = os.path.join(dir_path, filename)
    with urllib.request.urlopen(url) as uf:
        with open(file_path, 'bw') as of:
            of.write(uf.read())
        print('download pdf.')
        if not os.path.exists(file_path):
            print('download failed.')
    return file_path


class LocalPaperDirectory:
    # ディレクトリの状況に同期，管理を行う予定，
    def __init__(self, watch):
        cache_dir = init_cache_dir()
        self.obs = None
        if watch:
            self.start_watching(cache_dir)

    def __del__(self):
        if self.obs:
            self.stop_watching()

    def get_result_html_path(self, url_or_path):
        cache_dir = init_cache_dir()
        _, filename = os.path.split(url_or_path)
        working_dir = init_working_dir(cache_dir, filename)
        basename, _ = os.path.splitext(filename)
        # cache_dir/basename/basename_0.html
        result_html = os.path.join(working_dir, f"{basename}_0.html")
        return result_html

    def download2working_dir(self, url):
        cache_dir = init_cache_dir()
        _, filename = os.path.split(url)
        working_dir = init_working_dir(cache_dir, filename)
        return download(url, working_dir)

    def is_converted(self, url_or_path):
        return os.path.exists(self.get_result_html_path(url_or_path))

    def prepare_html(self, download_url):
        if self.is_converted(download_url):
            # cache_dir/basename/basename_0.html
            return self.get_result_html_path(download_url)
        else:
            pdf_filename = self.download2working_dir(download_url)
            result_html = paper2one_html(pdf_filename, cache_dir, debug)
            print('output html file')
            return result_html

    def _is_time_to_convert(self, event):
        base_dir, filename = os.path.split(event.src_path)

        # to ignore intermediate pdf files on some OS (recursive option does not work... ?)
        if not os.path.samefile(base_dir, init_cache_dir()):
            return False

        # already converted
        if self.is_converted(filename):
            return False

        return True

    def _store_pdf(self, pdf_path):
        _, filename = os.path.split(pdf_path)
        stored_pdf_path = os.path.join(init_working_dir(init_cache_dir(), filename), filename)
        shutil.move(pdf_path, stored_pdf_path)

    def on_pdf_placed(self, event: FileSystemEvent):
        if self._is_time_to_convert(event):
            paper2one_html(event.src_path, init_cache_dir(), self.debug)
            self._store_pdf(event.src_path)

    def start_watching(self, dir_path):
        obs = Observer()
        event_handler = PdfFilePlacedEventHandler(self.on_pdf_placed,
            server_mode=(str(type(obs)) == "<class 'watchdog.observers.inotify.InotifyObserver'>"))
        obs.schedule(event_handler, os.path.abspath(dir_path), recursive=False)
        obs.start()
        return obs

    def stop_watching(self):
        obs = self.obs
        obs.unschedule_all()
        obs.stop()
        obs.join()


class PdfFilePlacedEventHandler(PatternMatchingEventHandler):
    def __init__(self, handler, case_sensitive=False, debug=False, server_mode=False):
        super().__init__(("*.pdf",), ignore_patterns=None, ignore_directories=True, case_sensitive=case_sensitive)
        self.handler = handler
        self.debug = debug
        self.server_mode = server_mode

    def _is_placed(self, event):
        # file server may write pdf file without locking.
        if self.server_mode and str(event.event_type) != 'closed':
            return False

        if not os.path.exists(event.src_path):
            return False
        
        return True

    def on_any_event(self, event: FileSystemEvent):
        if self._is_placed(event):
            self.handler(event)


def convert_service_run(host, port, watch, debug):
    paper_dir = LocalPaperDirectory(watch)

    app = Flask(__name__)
    @app.route('/paper2html')
    def render():
        download_url = request.args.get('url')
        app.logger.debug(download_url)
        _, ext = os.path.splitext(download_url)
        if ext != ".pdf":
            return f"{download_url} is not url to pdf."

        result_html = paper_dir.prepare_html(download_url)
        return send_file(result_html, mimetype='text/html')

    @app.errorhandler(500)
    def server_error(e):
        logging.exception('An error occurred during a request.')
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500

    app.run(debug=debug, host=host, port=port)
