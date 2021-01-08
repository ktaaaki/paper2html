import re
import os
import math
from os.path import join as pjoin
from glob import glob
from .paper import PaperItemType, BBox
from . import templates


try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources


class LocalHtmlPaper:
    def __init__(self, paper, pdf_name):
        self.paper = paper
        self.pdf_name = pdf_name

    def _paragraph2txt(self, paragraph):
        """
        段落内の改行を取り除く．pdfからのコピペの整形に使用していたころの名残．
        """
        result = "".join([item.text for item in paragraph])
        patt = '([^(.|\n)])- ([^\n])'
        result = re.sub(patt, r'\1\2', result)
        patt = '([^(.|\n)])-\n([^\n])'
        result = re.sub(patt, r'\1\2', result)
        # patt = '\.\n'
        # result = re.sub(patt, r'.\n\n', result)
        patt = '([^(.|\n)])\n([^\n])'
        result = re.sub(patt, r'\1 \2', result)
        result = re.sub("([^\\.])\n", r"\1 ", result)
        return result + "\n"

    def _paragraph2img_elem(self, paragraph, i):
        img_template = '<p id="img{}"><img alt="Figure" src="./{}" /></p>\n'
        if paragraph[0].type == PaperItemType.Figure:
            return img_template.format(i, os.path.relpath(paragraph[0].url, self.paper.output_dir))
        else:
            return "\n".join([img_template.format(i, os.path.relpath(item.url, self.paper.output_dir)) for item in paragraph])

    def _paragraph2txt_elem(self, paragraph, i):
        txt_template = '<p id="txt{}">{}</p>\n'
        if len(paragraph) == 0:
            return ""
        if paragraph[0].type == PaperItemType.SectionHeader:
            return '<h2 id="txt{}">{}</h2>\n'.format(i, self._paragraph2txt(paragraph))
        elif paragraph[0].type == PaperItemType.Figure:
            return txt_template.format(i, "")
        else:
            return txt_template.format(i, self._paragraph2txt(paragraph))

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
            return '<h2 data-address="{}" id="txt{}">{}</h2>\n'.format(address_str, i, self._paragraph2txt(paragraph))
        elif paragraph[0].type == PaperItemType.Figure:
            return img_template.format(address_str, i, os.path.relpath(paragraph[0].url, self.paper.output_dir))
        else:
            return txt_template.format(address_str, i, self._paragraph2txt(paragraph))

    @staticmethod
    def _chunks(list, n):
        if n == math.inf:
            yield list
            return
        for i in range(0, len(list), n):
            yield list[i:i + n]

    def _export_patched_htmls(self, css_rel_path):
        top_html_template = '''
            <!DOCTYPE html>
            <html lang="en">
              <head>
                <meta http-equiv="Content-type" content="text/html;charset=utf-8" />
                <link href="{}" rel="stylesheet" type="text/css" />
                <title>
                  {}
                </title>
              </head>
              <body>
                <div id="split">
                  <header style="position: fixed;">
                    <input type="button" value="30%" onclick="Zoom(0.33);"/>
                    <input type="button" value="50%" onclick="Zoom(0.5);"/>
                    <input type="button" value="65%" onclick="Zoom(0.65);"/>
                    <input type="button" value="100%" onclick="Zoom(1);"/>
                    <a href="{}">[Original PDF]</a>
                  </header><br />
                  <div id="left">
                      {}
                  </div>
                  <div id="right">
                      {}
                  </div>
                </div>
                {}
              </body>
            </html>
        '''
        javascript = r'''
        <script language="javascript" type="text/javascript">
            const Zoom = function(rate) {
                for (let i = 0; i < document.images.length; i++) {
                    document.images[i].width = document.images[i].naturalWidth * rate;
                    document.images[i].height = document.images[i].naturalHeight * rate;
                }
            }
            const rightw = document.getElementById('right');
            const leftw = document.getElementById('left');
            const split = document.getElementById( 'split' );

            var onscrollR = function() {
             const top_ = split.scrollTop;
             const bottom_ = top_ + split.clientHeight;
             const center_ = (2/3) * top_ + (1/3) * bottom_;
             for(var i = 0; i < rightw.children.length; i++) {
              const txt_line = rightw.children[i];
              const rect = txt_line.getBoundingClientRect();
                if (rect.top <= center_ && center_ <= rect.bottom)
                {
                  const delta_rate = (center_ - rect.top) / rect.height;
                  const img_line = document.getElementById(txt_line.id.replace('txt', 'img'));
                  const delta_ = delta_rate * img_line.offsetHeight;
                  leftw.scrollTo(0, img_line.offsetTop + delta_ - center_);
                  break;
                }
              }
            }
            if( rightw.addEventListener )
            {
                rightw.addEventListener('scroll', onscrollR, false);
            }
        </script>
        '''

        html_pages = []
        for paragraphs in self._chunks(self.paper.paragraphs, self.paper.n_div_paragraph):
            img_content = "\n\n\n\n\n".join(
                [self._paragraph2img_elem(paragraph, i) for i, paragraph in enumerate(paragraphs)])
            txt_content = "\n\n\n\n\n".join(
                [self._paragraph2txt_elem(paragraph, i) for i, paragraph in enumerate(paragraphs)])

            html_pages.append([img_content, txt_content])

        html_files = []
        for i, page in enumerate(html_pages):
            img_column, txt_column = page
            output_filename = self.pdf_name + '_%d.html' % i
            output_path = pjoin(self.paper.output_dir, output_filename)
            with open(output_path, 'w', encoding="utf-8_sig") as f:
                original_link = self.paper.output_dir + '.pdf'
                top_html_template = pkg_resources.read_text(templates, "two_panes_with_patch.html")
                javascript = pkg_resources.read_text(templates, "two_panes_with_patch.js")
                f.write(top_html_template.format(css_rel_path, self.pdf_name, original_link,
                                                 img_column, txt_column, javascript))
            html_files.append(output_path)
        return html_files

    def _export_zoomed_htmls(self, css_rel_path):
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
                original_link = self.paper.output_dir + '.pdf'
                # TODO: ページ切り替えをどうするか→上下の矩形に含まれるページを両方ズームで表示して並べる，矩形外はマスクせず重ねない
                # slot: css_rel_path, title, original url, right pane, script
                top_html_template = pkg_resources.read_text(templates, "two_panes_with_zoom.html")
                # TODO: コンテナにcanvasを載せてスクロールを実現する，コンテナにブラウザ上のサイズをもたせる．canvasのサイズは表示する論文のサイズからステップごとに変更される．
                # slot: paper_img_paths
                javascript = pkg_resources.read_text(templates, "two_panes_with_zoom.js")
                f.write(top_html_template.format(css_rel_path, self.pdf_name, original_link, page,
                                                 javascript.replace("####", str(original_image_paths))))
            html_files.append(output_path)
        return html_files

    def _bbox2pixel(self, bbox, page_n):
        page = self.paper.pages[page_n]
        assert bbox.orig == 'LB'
        return (*page._pt2pixel(bbox.left, bbox.top), *page._pt2pixel(bbox.right, bbox.bottom))

    def export(self):
        css_rel_path = pjoin('resources', 'stylesheet.css')
        css_filename = pjoin(self.paper.output_dir, css_rel_path)
        with open(css_filename, 'w', encoding="utf-8_sig") as f:
            f.write(pkg_resources.read_text(templates, 'stylesheet.css'))

        return self._export_zoomed_htmls(css_rel_path)
