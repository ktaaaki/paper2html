# -*- coding:utf-8 -*-
# paper2html/paper2html/paper_miner.py
# This file is licensed under the MIT license (see LICENSE_MIT for details)
# Copyright (C) 2021 ktaaaki
import math
import os
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine, LTFigure, LTLine, LTCurve, \
    LTTextBoxHorizontal, LTTextBoxVertical, LTImage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from paper2html.paper import Paper, PaperItemType, PaperItem, PaperPage, BBox
from paper2html.html_paper import HtmlPaper


def read_by_extended_pdfminer(pdf_filename, line_margin_rate=None, verbose=False):
    paper = PaperReader().read(pdf_filename, line_margin_rate)
    if verbose:
        paper.show_layouts()

    _, pdf_name = os.path.split(pdf_filename)
    pdf_name, _ = os.path.splitext(pdf_name)
    urls = HtmlPaper(paper, pdf_name).export()
    return urls


class PaperReader:
    """
    pdfminerを使用してpdfファイルからPaperオブジェクトを作成するクラス．
    """
    def __init__(self):
        self.laparams = LAParams()

    @staticmethod
    def _pdf_pages(pdf_filename):
        with open(pdf_filename, 'rb') as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)

            for page in PDFPage.create_pages(doc):
                yield page

    def _lt_pages(self, pdf_filename):
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=self.laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in self._pdf_pages(pdf_filename):
            interpreter.process_page(page)
            yield device.get_result()

    def read(self, pdf_filename, line_margin_rate=None):
        # laparams.line_margin = 0.3
        self.laparams.boxes_flow = 1.0  # 1.0: vertical order, -1.0: horizontal order
        # self.laparams.detect_vertical = True
        # laparams.all_texts = True
        self._zap(pdf_filename)
        if line_margin_rate:
            self.laparams.line_margin = line_margin_rate

        paper = Paper(self.line_height, self.line_margin)

        for page_number, ltpage in enumerate(self._lt_pages(pdf_filename)):
            page = PaperPage(BBox(ltpage.bbox, orig='LB'), page_number)
            for item in ltpage:
                self._render_item(page, item, page_number)
            paper.add_page(page)
        return paper

    def _zap(self, pdf_filename):
        """
        先頭2ページを調べ，行の高さと行間の最頻値からpdfminer.Lparams.line_margin = 行間/行の高さ を設定します．
        """
        line_margin_counts = {}
        line_height_counts = {}
        zap_max = 2
        for page_number, ltpage in enumerate(self._lt_pages(pdf_filename)):
            if page_number > zap_max:
                break
            self._count_line_properties(ltpage, line_margin_counts, line_height_counts)

        self.line_height = 10
        if line_height_counts:
            self.line_height = sorted(list(line_height_counts.items()), key=lambda item: -item[1])[0][0]
        self.line_margin = self.line_height * self.laparams.line_margin
        if line_margin_counts:
            self.line_margin = sorted(list(line_margin_counts.items()), key=lambda item: -item[1])[0][0]
        self.laparams.line_margin = self.line_margin / self.line_height
        print('line_height: {}\nline_margin: {}'.format(self.line_height, self.line_margin))

    def _count_line_properties(self, item, line_margin_counts, line_height_counts):
        """
        検出されたTextLineに対していくつかの統計を取る
        """
        if isinstance(item, LTPage):
            for child in item:
                self._count_line_properties(child, line_margin_counts, line_height_counts)
        elif isinstance(item, LTTextBoxHorizontal):
            prev_line = None
            for child in item:
                if isinstance(child, LTTextLine):
                    if child.height not in line_height_counts:
                        line_height_counts[child.height] = 0
                    line_height_counts[child.height] += 1

                    if not prev_line:
                        continue
                    prev_line_bbox = BBox(prev_line.bbox, orig='LB')
                    child_bbox = BBox(child.bbox, orig='LB')
                    margin = abs(prev_line_bbox.bottom - child_bbox.top)
                    if margin not in line_margin_counts:
                        line_margin_counts[margin] = 0
                    line_margin_counts[margin] += 1
                    prev_line = child

    @staticmethod
    def _char_is_horizontal(char):
        """
        文字の配置行列から横書きの文字であるかを判定する
        """
        h_rot = math.atan2(char.matrix[1], char.matrix[0])
        v_rot = math.atan2(char.matrix[3], char.matrix[2])
        h_rot2 = v_rot - math.pi/2
        sigma = math.pi/8
        return -sigma < h_rot < sigma and -sigma < h_rot2 < sigma

    def _textbox_is_vertical(self, text_box):
        """
        英文テキストが縦書きされているか判定する
        """
        # detect vertical text box
        MAX_CHECK_NUM = 10
        checked_char_num = 0
        vertical_char_num = 0
        horizontal_char_num = 0
        for child in text_box:
            if not isinstance(child, LTTextLine):
                continue
            for cchild in child:
                if not isinstance(cchild, LTChar):
                    continue
                if self._char_is_horizontal(cchild):
                    horizontal_char_num += 1
                else:
                    vertical_char_num += 1
                checked_char_num += 1
                if checked_char_num >= MAX_CHECK_NUM:
                    return horizontal_char_num < vertical_char_num
        return horizontal_char_num < vertical_char_num

    def _render_item(self, page, item, page_number):
        separated = False
        if isinstance(item, LTTextBoxHorizontal):
            self._render_textbox(page, item, page_number)
        elif isinstance(item, (LTLine, LTCurve)):
            self._render_shape(page, item, page_number)
        elif isinstance(item, (LTFigure, LTImage)):
            self._render_figure(page, item, page_number)
        elif isinstance(item, LTTextBoxVertical):
            item_type = PaperItemType.VTextBox
            text = item.get_text()
            page.add_item(PaperItem([item], page_number, BBox(item.bbox, orig='LB'), text, item_type, separated))
        else:
            print(type(item))

    def _render_textbox(self, page, textbox, page_number):
        if self._textbox_is_vertical(textbox):
            item_type = PaperItemType.VTextBox
        else:
            item_type = PaperItemType.TextBox
        page.add_item(PaperItem([textbox], page_number, BBox(textbox.bbox, orig='LB'),
                                textbox.get_text(), item_type))

    def _render_shape(self, page, item, page_number):
        bbox = BBox(item.bbox, orig='LB')
        item_type = PaperItemType.Shape
        text = "\n\n\n\n"
        # 幅0でclipするとエラーなので膨らませておく
        bbox = bbox.inflate(1)
        page.add_item(PaperItem([item], page_number, bbox, text, item_type, False))

    def _render_figure(self, page, item, page_number):
        item_type = PaperItemType.Figure
        text = "Figure Space\n\n\n\n"
        if hasattr(item, "__iter__"):
            # broken paragraph
            raw_text = [raw_char.get_text() for raw_char in item if isinstance(raw_char, LTChar)]
            if raw_text:
                item_type = PaperItemType.TextBox
                text = "".join(raw_text)
            for child in item:
                if isinstance(child, LTChar):
                    continue
                self._render_item(page, child, page_number)
        page.add_item(PaperItem([item], page_number, BBox(item.bbox, orig='LB'), text, item_type, False))
