import os
import time
import subprocess
from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path


def test_convert_service_run():
    p = subprocess.Popen(['python', os.path.join('paper2html', 'main.py')], shell=False)
    driver = webdriver.Chrome()
    driver.get('http://localhost:5000/paper2html/index.html')
    time.sleep(1)
    driver.get("http://localhost:5000/paper2html/convert?url=https%3A%2F%2Farxiv.org%2Fpdf%2F1609.05473.pdf")
    # search_box = driver.find_element_by_name("q")
    # search_box.send_keys('ChromeDriver')
    # search_box.submit()
    # time.sleep(1)
    driver.quit()
    p.kill()
