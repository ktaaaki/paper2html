import re
import os
import math
from os.path import join as pjoin
from .paper import PaperItemType


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

    def _paragraph2elem(self, paragraph, i):
        txt_template = '<p id="txt{}">{}</p>\n'
        img_template = '<p id="txt{}"><img alt="Figure" src="./{}" /></p>\n'
        if len(paragraph) == 0:
            return ""
        if paragraph[0].type == PaperItemType.SectionHeader:
            return '<h2 id="txt{}">{}</h2>\n'.format(i, self._paragraph2txt(paragraph))
        elif paragraph[0].type == PaperItemType.Figure:
            return img_template.format(i, os.path.relpath(paragraph[0].url, self.paper.output_dir))
        else:
            return txt_template.format(i, self._paragraph2txt(paragraph))

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
                f.write(top_html_template.format(css_rel_path, self.pdf_name, original_link,
                                                 img_column, txt_column, javascript))
            html_files.append(output_path)
        return html_files

    def _export_zoomed_htmls(self, css_rel_path):
        # slot: css_rel_path, title, original url, right pane, script
        top_html_template = r'''
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
                    <a href="{}">[Original PDF]</a>
                  </header><br />
                  <div id="left">
                      <canvas id="canvas"></canvas>
                  </div>
                  <div id="right">
                      {}
                  </div>
                </div>
                {}
              </body>
            </html>
        '''
        # TODO: ページ切り替えをどうするか→上下の矩形に含まれるページを両方ズームで表示して並べる，矩形外はマスクせず重ねない
        # TODO: 画像出力したpathを入手する（削除しない）
        # slot: paper_img_path, 
        javascript = r'''
    <script language="javascript" type="text/javascript">
      const img_path = "{}";

      const rightw = document.getElementById('right');
      const leftw = document.getElementById('left');
      const split = document.getElementById( 'split' );

      var canvas = document.getElementById('canvas');
      canvas.width = leftw.clientWidth;
      canvas.height = leftw.clientHeight;
      rightw.style.paddingTop = String(rightw.clientHeight*(1./4.))+"px";
      rightw.style.paddingBottom = String(rightw.clientHeight*(3./4.))+"px";
      var c = canvas.getContext('2d');
      var zoom_rate = 1;

      // Image オブジェクトを生成
      var img = new Image();
      img.src = img_path;

      img.onload = function(){
          zoom_rate = Math.min(canvas.width/img.width, canvas.height/img.height);
          // 拡大
          c.scale(zoom_rate, zoom_rate);
          c.drawImage(img, 0, 0);

      }

      const Zoom = function(rate) {
          for (let i = 0; i < document.images.length; i++) {
              document.images[i].width = document.images[i].naturalWidth * rate;
              document.images[i].height = document.images[i].naturalHeight * rate;
          }
      }

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
            //const img_line = document.getElementById(txt_line.id.replace('txt', 'img'));
            //const delta_ = delta_rate * img_line.offsetHeight;
            //leftw.scrollTo(0, img_line.offsetTop + delta_ - center_);
            //c.clearRect(0, 0, c.canvas.width, c.canvas.height);
            c.fillStyle = "rgba(255, 255, 255, 255)";
            c.fillRect(0, 0, canvas.width/zoom_rate, canvas.height/zoom_rate);
            c.drawImage(img, rect.top, rect.top);
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
            # TODO: ページ番号と対応矩形を手に入れ，elemに内包させる
            content = "\n\n\n\n\n".join(
                [self._paragraph2elem(paragraph, i) for i, paragraph in enumerate(paragraphs)])

            html_pages.append(["bbox", content])

        html_files = []
        for i, page in enumerate(html_pages):
            img_column, txt_column = page
            output_filename = self.pdf_name + '_%d.html' % i
            output_path = pjoin(self.paper.output_dir, output_filename)
            with open(output_path, 'w', encoding="utf-8_sig") as f:
                original_link = self.paper.output_dir + '.pdf'
                f.write(top_html_template.format(css_rel_path, self.pdf_name, original_link,
                                                 img_column, txt_column, javascript))
            html_files.append(output_path)
        return html_files

    def export(self):
        css_content = '''
        html, body {
            height: 100%;
            overflow: hidden;
            margin: 0;
        }
        #split{
            height: 100%;
        }
        #left {
            float: left;
            top: 0;
            width: 50%;
            height: 100%;
            overflow: auto;
            box-sizing: border-box;
            z-index: 1;
            padding: 50% 1.5em 50%;
        }
        #right{
            float: left;
            top: 0;
            left: 50%;
            width: 50%;
            height: 100%;
            overflow: auto;
            box-sizing: border-box;
            z-index: 2;
            background-color: #FFFFFF;
            padding: 50% 1.5em 50%;
        }
        '''
        css_rel_path = pjoin('resources', 'stylesheet.css')
        css_filename = pjoin(self.paper.output_dir, css_rel_path)
        with open(css_filename, 'w', encoding="utf-8_sig") as f:
            f.write(css_content)

        return self._export_patched_htmls(css_rel_path)
