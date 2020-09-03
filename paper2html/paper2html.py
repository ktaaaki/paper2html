# -*- coding:utf-8 -*-
import os
from os.path import join as pjoin
from shutil import rmtree
import webbrowser
import fire
import pdf2image
from paper2html.paper import PaperPage, Paper
from paper2html.paper_miner import read_by_extended_pdfminer


def init_working_dir(base_dir=None):
    if not base_dir:
        base_dir = pjoin(os.environ['HOME'], 'paper2html')
    fixed_dir = pjoin(base_dir, 'fixed_pdf')
    output_dir = pjoin(base_dir, 'output')
    image_dir = pjoin(base_dir, 'original_images')
    crop_dir = pjoin(base_dir, 'crops')
    layout_dir = pjoin(base_dir, 'layout')
    Paper.output_dir = output_dir
    Paper.layout_dir = layout_dir
    PaperPage.image_dir = image_dir
    PaperPage.crop_dir = crop_dir

    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    for dir_name in (output_dir, image_dir, crop_dir, layout_dir, fixed_dir):
        if os.path.exists(dir_name):
            rmtree(dir_name)
        os.mkdir(dir_name)
    return fixed_dir, image_dir


def open_by_browser(filename, browser_path=None):
    full_path = os.path.abspath(filename)
    url = "file://" + full_path
    if browser_path:
        browser = webbrowser.get('"{}" %s'.format(browser_path))
        browser.open(url)
    else:
        webbrowser.open(url)


def clean_pdf(pdf_filename, output_dir):
    import subprocess
    _, base_name = os.path.split(pdf_filename)
    new_pdf_filename = pjoin(output_dir, base_name)
    subprocess.run(['mutool', 'clean', pdf_filename, new_pdf_filename])
    return new_pdf_filename


def open_paper_htmls(pdf_filename, working_dir=None, browser_path=None):
    """
    処理の流れ：
        破損したpdfを修復
        pdf2imageでpdfの画像取得
        pdfminerに解析結果とともに返してもらう
        解析結果であるPaperのshow_layoutsとget_htmlsを呼び出して結果を得る
    """
    fixed_dir, image_dir = init_working_dir(working_dir)
    pdf_filename = clean_pdf(pdf_filename, fixed_dir)
    pdf2image.convert_from_path(pdf_filename, output_folder=image_dir, output_file='pdf', paths_only=True)
    urls = read_by_extended_pdfminer(pdf_filename)

    for url in urls:
        open_by_browser(url, browser_path)


if __name__ == '__main__':
    fire.Fire(open_paper_htmls)
