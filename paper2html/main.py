import argparse
from paper2html.convert_service import convert_service_run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=bool, default=False)
    parser.add_argument("--host", type=str, default="127.0.0.1", help="use 0.0.0.0 if you use it on a server.")
    parser.add_argument("--port", type=int, default=5000, help="use 80 if you use it on a server.")
    parser.add_argument("--watch", type=bool, default=False,
                        help="automatically convert local PDFs on the paper_cache directory.")
    args = parser.parse_args()

    convert_service_run(args.host, args.port, args.watch, args.debug)
