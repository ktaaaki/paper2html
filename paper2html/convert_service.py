import logging
import os

from flask import Flask, request, send_file
from paper2html.local_paper_directory import LocalPaperDirectory


def convert_service_run(host, port, watch, debug):
    paper_dir = LocalPaperDirectory(watch, debug)

    app = Flask(__name__)

    @app.route('/paper2html/convert')
    def render():
        download_url = request.args.get('url')
        app.logger.debug(download_url)
        _, ext = os.path.splitext(download_url)
        if ext != ".pdf":
            return f"{download_url} is not url to pdf."

        result_html = paper_dir.prepare_html(download_url)
        return send_file(os.path.abspath(result_html), mimetype='text/html')

    @app.route('/paper2html/index.html')
    def browse_top():
        def url_factory(filename):
            print(app.root_path)
            return f"http://localhost:5000/paper2html/browse/{filename}"
        index_html = paper_dir.update_index_html(url_factory)
        return send_file(os.path.abspath(index_html), mimetype='text/html')

    @app.route('/paper2html/browse/<filename>')
    def browse(filename):
        result_html = paper_dir.prepare_html(filename)
        return send_file(os.path.abspath(result_html), mimetype='text/html')

    @app.errorhandler(500)
    def server_error(e):
        logging.exception('An error occurred during a request.')
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500

    app.run(debug=debug, host=host, port=port)
