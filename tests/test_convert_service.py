import time
import os
from os.path import join as pjoin, abspath
import pathlib
from multiprocessing import Process
import selenium.common.exceptions
from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path

import paper2html


def test_convert_service_run():
    p = Process(target=paper2html.convert_service_run, args=("0.0.0.0", 5000, None, True, False))
    p.start()
    driver = webdriver.Chrome()
    driver.get('http://localhost:5000/paper2html/index.html')
    time.sleep(1)
    test_dir, _ = os.path.split(__file__)
    pdf_uri = pathlib.Path(abspath(pjoin(test_dir, 'sample_files', 'one_column.pdf'))).as_uri()
    url = f"http://localhost:5000/paper2html/convert?url={pdf_uri}"
    driver.get(url)
    try:
        driver.find_element_by_id("right")
    except selenium.common.exceptions.NoSuchElementException:
        raise Exception("no output html")
    finally:
        driver.close()
        p.terminate()
