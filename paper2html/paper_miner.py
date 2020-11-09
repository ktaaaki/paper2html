import os
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine, LTFigure, LTLine, LTCurve, \
    LTTextBoxHorizontal, LTTextBoxVertical, LTImage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from .paper import Paper, PaperItemType, PaperItem, PaperPage, unify_bboxes
from .local_html_paper import LocalHtmlPaper


def read_by_extended_pdfminer(pdf_filename, line_margin_rate=None, verbose=False):
    paper = PaperReader(pdf_filename, line_margin_rate).read()
    if verbose:
        paper.show_layouts()

    _, pdf_name = os.path.split(pdf_filename)
    pdf_name, _ = os.path.splitext(pdf_name)
    urls = LocalHtmlPaper(paper, pdf_name).export()
    return urls


class PaperReader:
    def __init__(self, pdf_filename, line_margin_rate=None):
        self.pdf_filename = pdf_filename
        self.laparams = LAParams()
        # laparams.line_margin = 0.3
        self.laparams.boxes_flow = 1.0  # 1.0: vertical order, -1.0: horizontal order
        # self.laparams.detect_vertical = True
        # laparams.all_texts = True
        if not line_margin_rate:
            self._zap()
        else:
            self.laparams.line_margin = line_margin_rate

    def pdf_pages(self):
        with open(self.pdf_filename, 'rb') as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)

            for page in PDFPage.create_pages(doc):
                yield page

    def lt_pages(self):
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=self.laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in self.pdf_pages():
            interpreter.process_page(page)
            yield device.get_result()

    def read(self):
        paper = Paper(self.line_height, self.line_margin)

        for page_number, ltpage in enumerate(self.lt_pages()):
            page = PaperPage(ltpage.bbox, page_number)
            for item in ltpage:
                self.render_item(page, item, page_number)
            paper.add_page(page)
        return paper

    def _zap(self):
        """
        先頭2ページを調べ，行の高さと行間の最頻値からpdfminer.Lparams.line_margin = 行間/行の高さ を設定します．
        """
        line_margin_counts = {}
        line_height_counts = {}
        zap_max = 2
        for page_number, ltpage in enumerate(self.lt_pages()):
            if page_number > zap_max:
                break
            self._count_something(ltpage, line_margin_counts, line_height_counts)

        self.line_height = 10
        if line_height_counts:
            self.line_height = sorted(list(line_height_counts.items()), key=lambda item: -item[1])[0][0]
        self.line_margin = self.line_height * self.laparams.line_margin
        if line_margin_counts:
            self.line_margin = sorted(list(line_margin_counts.items()), key=lambda item: -item[1])[0][0]
        self.laparams.line_margin = self.line_margin / self.line_height
        print('line_height: {}\nline_margin: {}'.format(self.line_height, self.line_margin))

    def _count_something(self, item, line_margin_counts, line_height_counts):
        """
        検出されたTextLineに対していくつかの統計を取る
        """
        if isinstance(item, LTPage):
            for child in item:
                self._count_something(child, line_margin_counts, line_height_counts)
        elif isinstance(item, LTTextBoxHorizontal):
            prev_line = None
            for child in item:
                if isinstance(child, LTTextLine):
                    if child.height not in line_height_counts:
                        line_height_counts[child.height] = 0
                    line_height_counts[child.height] += 1

                    if not prev_line:
                        continue
                    margin = prev_line.bbox[1] - child.bbox[3]
                    if margin not in line_margin_counts:
                        line_margin_counts[margin] = 0
                    line_margin_counts[margin] += 1
                    prev_line = child

    @staticmethod
    def _char_is_horizontal(char):
        """
        文字の配置行列から横書きの文字であるかを判定する
        """
        return abs(char.matrix[0] - char.matrix[3]) < 0.1 and abs(char.matrix[1] - 0) < 0.1 \
               and abs(char.matrix[2] - 0) < 0.1 and char.matrix[0] > 0 and char.matrix[3] > 0

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

    def _check_separated(self, text_box):
        mean_width = 0
        mean_height = 0
        max_x = text_box.bbox[0]
        char_count = 0
        for child in text_box:
            if isinstance(child, LTChar):
                char_count += 1
                mean_height += child.bbox[3] - child.bbox[1]
                mean_width += child.bbox[2] - child.bbox[0]
                max_x = max(child.bbox[2], max_x)
        if char_count == 0:
            return False
        mean_height /= char_count
        mean_width /= char_count

        last_child = None
        for child in text_box:
            if isinstance(child, LTChar) and child.bbox[1] < text_box.bbox[1] + mean_height:
                if not last_child:
                    last_child = child
                elif last_child.bbox[2] < child.bbox[2]:
                    last_child = child
        if last_child:
            separated = True
            if last_child.bbox[2] < max_x - mean_width:
                separated = False
            if last_child.get_text() == '.':
                separated = False
            return separated
        else:
            return False

    def render_item(self, page, item, page_number):
        separated = False
        if isinstance(item, LTTextBoxHorizontal):
            self.render_textbox(page, item)
        elif isinstance(item, (LTLine, LTCurve)):
            self.render_shape(page, item)
        elif isinstance(item, (LTFigure, LTImage)):
            self.render_figure(page, item, page_number)
        elif isinstance(item, LTTextBoxVertical):
            item_type = PaperItemType.VTextBox
            text = item.get_text()
            page.items.append(PaperItem(item.bbox, text, item_type, separated))
        else:
            print(type(item))

    def render_textbox(self, page, textbox):
        separated = False
        if self._textbox_is_vertical(textbox):
            item_type = PaperItemType.VTextBox
        else:
            item_type = PaperItemType.TextBox
            separated = self._check_separated(textbox)

        for paragraph in self._split_by_indent(textbox, item_type, separated):
            page.items.append(paragraph)

    def _split_by_indent(self, textbox, item_type, separated):
        bbox = textbox.bbox
        split_lines = [[]]
        lines = list(textbox)

        def is_indented(line):
            return line.bbox[0] - bbox[0] > self.line_height
        for i, line in enumerate(lines):
            if is_indented(line):
                if not i + 1 < len(lines):
                    split_lines.append([])
                elif not is_indented(lines[i + 1]):
                    split_lines.append([])
            split_lines[-1].append(line)
        if len(split_lines) == 0:
            raise ValueError('empty textbox.')
        if len(split_lines[0]) == 0:
            split_lines.pop(0)
        results = []
        for lines in split_lines:
            bbox = unify_bboxes([line.bbox for line in lines])
            text = ''.join([line.get_text() for line in lines])
            results.append(PaperItem(bbox, text, item_type, True))
        if len(results) == 0:
            raise ValueError('empty textbox.')
        results[0].separated = separated
        return results

    def render_shape(self, page, item):
        bbox = item.bbox
        item_type = PaperItemType.Shape
        text = "\n\n\n\n"
        # 幅0でclipするとエラーなので膨らませておく
        bbox = (bbox[0] - 1, bbox[1] - 1, bbox[2] + 1, bbox[3] + 1)
        page.items.append(PaperItem(bbox, text, item_type, False))

    def render_figure(self, page, item, page_number):
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
                self.render_item(page, child, page_number)
        page.items.append(PaperItem(item.bbox, text, item_type, False))
