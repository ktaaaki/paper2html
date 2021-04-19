import re
import os
import math
import base64
from io import BytesIO
from os.path import join as pjoin
from glob import glob
from PIL import Image
from paper2html.paper import PaperItemType, BBox
from paper2html import templates


try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources


class HtmlPaper:
    def __init__(self, paper, pdf_name):
        self.paper = paper
        self.pdf_name = pdf_name

    def _get_zoomed_pixel(self, paper_item):
        column_bbox = self.paper.pages[paper_item.page_n].address_bbox(paper_item.address)
        assert column_bbox.orig == 'LB' and paper_item.bbox.orig == 'LB'
        zoomed_bbox = BBox((column_bbox.left, paper_item.bbox.bottom, column_bbox.right, paper_item.bbox.top), orig='LB')
        result = self._bbox2pixel(zoomed_bbox, paper_item.page_n)
        return result

    def _paragraph2elem(self, paragraph, i):
        txt_template = '<p data-address="{}" id="txt{}">{}</p>\n'
        img_template = '<p data-address="{}" id="txt{}"><img alt="Figure" src="./{}" /></p>\n'
        if len(paragraph) == 0:
            return ""
        address_2d = [(paper_item.page_n, *self._get_zoomed_pixel(paper_item)) for paper_item in paragraph]
        address_str = "|".join(",".join([str(i) for i in item_addr]) for item_addr in address_2d)
        if paragraph[0].type == PaperItemType.SectionHeader:
            return '<h2 data-address="{}" id="txt{}">{}</h2>\n'.format(address_str, i, paragraph.content)
        elif paragraph[0].type == PaperItemType.Figure:
            return img_template.format(address_str, i, os.path.relpath(paragraph[0].url, self.paper.output_dir))
        else:
            return txt_template.format(address_str, i, paragraph.content)

    @staticmethod
    def _chunks(list, n):
        if n == math.inf:
            yield list
            return
        for i in range(0, len(list), n):
            yield list[i:i + n]

    def _export_zoomed_htmls(self, css_rel_path, inline):
        html_pages = []
        for paragraphs in self._chunks(self.paper.paragraphs, self.paper.n_div_paragraph):
            content = "".join(
                [self._paragraph2elem(paragraph, i) for i, paragraph in enumerate(paragraphs)])
            html_pages.append(content)

        image_dir = self.paper.pages[0].image_dir
        original_image_paths = sorted([os.path.relpath(abspath, self.paper.output_dir) for abspath in glob(pjoin(image_dir, "*.png"))])
        html_files = []
        for i, page in enumerate(html_pages):
            output_filename = self.pdf_name + '_%d.html' % i
            output_path = pjoin(self.paper.output_dir, output_filename)
            with open(output_path, 'w', encoding="utf-8_sig") as f:
                # TODO: ダウンロードリンクを設定するか，変換前ページを出力する
                original_link = self.paper.output_dir + '.pdf'
                # ページ切り替えをどうするか→上下の矩形に含まれるページを両方ズームで表示して並べる，矩形外はマスクせず重ねない
                # slot: css_rel_path, title, original url, right pane, non_display_imgs, script
                top_html_template = pkg_resources.read_text(templates, "two_panes_with_zoom.html")
                # コンテナにcanvasを載せてスクロールを実現する，コンテナにブラウザ上のサイズをもたせる．canvasのサイズは表示する論文のサイズからステップごとに変更される．
                # slot: paper_img_paths
                javascript = pkg_resources.read_text(templates, "two_panes_with_zoom.js")
                if inline:
                    css_content = pkg_resources.read_text(templates, "stylesheet.css")
                    css_part = f'<style type="text/css">\n<!--\n{css_content}\n-->\n</style>'
                else:
                    css_part = f'<link href="{css_rel_path}" rel="stylesheet" type="text/css" />'
                imgs = []
                for abspath in sorted(glob(pjoin(image_dir, "*.png"))):
                    relpath = os.path.relpath(abspath, self.paper.output_dir)
                    img = Image.open(abspath)
                    width, height = img.size
                    if inline:
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue())
                        src = "data:image/png;base64," + img_str.decode()
                    else:
                        src = relpath
                    img_elm = f'<img src="{src}" width="{width}" height="{height}" class="display_non" id="{relpath}">'
                    imgs.append(img_elm)
                imgs = '\n'.join(imgs)
                f.write(top_html_template.format(css_part, self.pdf_name, original_link, page,
                                                 imgs,
                                                 javascript.replace("####", str(original_image_paths))))
            html_files.append(output_path)
        return html_files

    def _bbox2pixel(self, bbox, page_n):
        page = self.paper.pages[page_n]
        assert bbox.orig == 'LB'
        return (*page._pt2pixel(bbox.left, bbox.top), *page._pt2pixel(bbox.right, bbox.bottom))

    def export(self, inline=True):
        css_rel_path = pjoin('resources', 'stylesheet.css')
        css_filename = pjoin(self.paper.output_dir, css_rel_path)
        with open(css_filename, 'w', encoding="utf-8_sig") as f:
            f.write(pkg_resources.read_text(templates, 'stylesheet.css'))

        return self._export_zoomed_htmls(css_rel_path, inline)
