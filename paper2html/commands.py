# -*- coding:utf-8 -*-
import math
import os
from os.path import join as pjoin
from shutil import rmtree
from glob import glob
import webbrowser
from urllib.parse import quote
import fire
import pdf2image
from paper2html.paper import PaperPage, Paper
from paper2html.paper_miner import read_by_extended_pdfminer


def _get_unique_dirname(dirname):
    i = 1
    if not os.path.exists(dirname):
        return dirname
    dirname = dirname + '-0'
    while os.path.exists(dirname):
        dirname = dirname[:-len(dirname.split('-')[-1])] + str(i)
        i += 1
    return dirname


def init_working_dir(working_dir, pdf_filename):
    base_dir, pdf_name = os.path.split(pdf_filename)
    pdf_name, _ = os.path.splitext(pdf_name)
    if not working_dir:
        working_dir = base_dir

    output_dir = _get_unique_dirname(pjoin(working_dir, pdf_name))
    resource_dir = pjoin(output_dir, 'resources')
    temp_dir = pjoin(output_dir, 'temp')

    crop_dir = pjoin(resource_dir, 'crops')
    fixed_dir = pjoin(temp_dir, 'fixed_pdf')
    image_dir = pjoin(temp_dir, 'original_images')
    layout_dir = pjoin(temp_dir, 'layout')

    Paper.output_dir = output_dir
    Paper.resource_dir = resource_dir
    Paper.layout_dir = layout_dir
    PaperPage.image_dir = image_dir
    PaperPage.crop_dir = crop_dir

    for dir_name in (output_dir, resource_dir, temp_dir,
                     crop_dir, fixed_dir, image_dir, layout_dir):
        os.mkdir(dir_name)
    return fixed_dir, image_dir, temp_dir


def open_by_browser(filename, browser_path=None):
    full_path = os.path.abspath(filename)
    url = "file://" + quote(full_path)
    if browser_path:
        browser = webbrowser.get('"{}" %s'.format(browser_path))
        browser.open(url)
    else:
        webbrowser.open(url)


def clean_pdf(pdf_filename, working_dir):
    """
    Fix broken pdf.
    @param pdf_filename:
        The target pdf file.
    @param working_dir:
        The directory for the fixed pdf.
    @return:
        The fixed pdf file.
    """
    import subprocess
    _, base_name = os.path.split(pdf_filename)
    new_pdf_filename = pjoin(working_dir, base_name)
    subprocess.run(['mutool', 'clean', pdf_filename, new_pdf_filename])
    return new_pdf_filename


def message_for_automator(msg):
    webbrowser.open("https://www.google.com/search?q={}".format(quote(msg)))


def paper2html(target_path: str, working_dir: str = None, verbose: bool = False) -> list:
    """
    Generate paper htmls from a pdf file.
    @param target_path:
        The target pdf file or the directory of pdf files.
    @param working_dir:
        The working directory contains output directory and html files.
        Default is the same directory as pdf_filename.
    @param verbose:
        Whether to output files which indicate the visual recognition process.
    @return: 
        List of url of generated htmls.
    """
    if os.path.isdir(target_path):
        urls = []
        for pdf_filename in glob(pjoin(target_path, "**", "*.pdf"), recursive=True):
            if os.path.isfile(pdf_filename):
                urls.extend(paper2html(pdf_filename, working_dir, verbose))
        return urls

    pdf_filename = target_path
    _, ext = os.path.splitext(pdf_filename)
    if ext != '.pdf' or not os.path.isfile(pdf_filename):
        raise ValueError('Only pdf files are supported')

    fixed_dir, image_dir, temp_dir = init_working_dir(working_dir, pdf_filename)
    pdf_filename = clean_pdf(pdf_filename, fixed_dir)
    pdf2image.convert_from_path(pdf_filename, output_folder=image_dir, output_file='pdf', paths_only=True)
    urls = read_by_extended_pdfminer(pdf_filename, verbose)

    if not verbose:
        rmtree(temp_dir)

    return urls


def open_paper_htmls(pdf_filename: str, working_dir: str = None, browser_path: str = None,
                     n_div_paragraph: int = 800, verbose: bool = False):
    """
    Open generated paper htmls from a pdf file with a browser.
    @param pdf_filename:
        The target pdf file.
    @param working_dir:
        The working directory contains output directory and html files.
        Default is the same directory as pdf_filename.
    @param browser_path:
        The browser to open the file with.
    @param n_div_paragraph:
        Number of paragraphs to combine in one output html.
    @param verbose:
        Whether to output files which indicate the visual recognition process.
    """
    Paper.n_div_paragraph = n_div_paragraph
    for url in paper2html(pdf_filename, working_dir, verbose):
        open_by_browser(url, browser_path)


if __name__ == '__main__':
    fire.Fire(open_paper_htmls)
