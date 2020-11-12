import re
import os
import math
from os.path import join as pjoin
from glob import glob
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
        txt_template = '<p data-address="{}" id="txt{}">{}</p>\n'
        img_template = '<p data-address="{}" id="txt{}"><img alt="Figure" src="./{}" /></p>\n'
        if len(paragraph) == 0:
            return ""
        address_2d = [(paper_item.page_n, *self._bbox2pixel(paper_item.bbox, paper_item.page_n)) for paper_item in paragraph]
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
                f.write(top_html_template.format(css_rel_path, self.pdf_name, original_link,
                                                 img_column, txt_column, javascript))
            html_files.append(output_path)
        return html_files

    def _export_zoomed_htmls(self, css_rel_path):
        # slot: css_rel_path, title, original url, right pane, script
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
        # slot: paper_img_paths
        javascript = r'''
<script language="javascript" type="text/javascript">
  // setup base elements
  const rightw = document.getElementById('right');
  const leftw = document.getElementById('left');
  const split = document.getElementById( 'split' );

  var canvas = document.getElementById('canvas');
  canvas.width = leftw.clientWidth;
  canvas.height = leftw.clientHeight;
  rightw.style.paddingTop = String(rightw.clientHeight*(1./4.))+"px";
  rightw.style.paddingBottom = String(rightw.clientHeight*(3./4.))+"px";
  var c = canvas.getContext('2d');

  // load all images
  // 直接ファイルリストをスクリプトに埋め込む
  const img_pathes = ####;

  var paper_imgs = {};
  var loaded_img_count = 0;
  function on_img_loaded(){
    // zoom_rate = Math.min(canvas.width/paper_imgs[0].width, canvas.height/paper_imgs[0].height);
    // // 拡大
    // c.scale(zoom_rate, zoom_rate);
    // c.drawImage(paper_imgs[0], 0, 0);
  }
  for(i = 0; i < img_pathes.length; i++){
    const img = new Image();
    const closure_i = i;
    img.src = img_pathes[i];
    img.onload = function(){
        paper_imgs[closure_i] = img;
        loaded_img_count++;
        if(loaded_img_count == img_pathes.length){
          on_img_loaded();
        }
    }
  }

  const parse_address = function(str_addr) {
    return str_addr.split('|').map(each_addr => {
      const num_strs = each_addr.split(',');
      const page_n = parseInt(num_strs[0]);
      const left = parseFloat(num_strs[1]);
      const top = parseFloat(num_strs[2]);
      const right = parseFloat(num_strs[3]);
      const bottom = parseFloat(num_strs[4]);
      return [page_n, left, top, right, bottom];
    });
  }
  const get_address = function(elem) {
    return parse_address(elem.getAttribute("data-address"));
  }


  const get_papers_transform = function(paper_size, canvas_size, target, center_height){
    const zoom = canvas_size[0]/target[2];
    const content_top = center_height/zoom - target[3]/2.;
    const content_left = 0;
    const left = -target[0] + content_left;
    const top = -target[1] + content_top;
    return [zoom, left, top];
  }

  var now_addr = [];
  var now_trsf = [];
  const onscrollR = function() {
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
        const addrs = get_address(txt_line);
        const addr = addrs[0];
        now_addr = addr;
        const paper_img = paper_imgs[addr[0]];
        const trsf = get_papers_transform(
          [paper_img.width, paper_img.height],
          [canvas.width, canvas.height],
          [addr[1], addr[2], addr[3]-addr[1], addr[4]-addr[2]],
          center_);
        now_trsf = trsf;
        c.fillStyle = "rgb(255, 255, 255)";
        c.fillRect(0, 0, canvas.width, canvas.height);
        c.save();
        c.scale(trsf[0], trsf[0]);
        c.drawImage(paper_img, trsf[1], trsf[2]);
        c.restore();
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
                f.write(top_html_template.format(css_rel_path, self.pdf_name, original_link, page,
                                                 javascript.replace("####", str(original_image_paths))))
            html_files.append(output_path)
        return html_files

    def _bbox2pixel(self, bbox, page_n):
        page = self.paper.pages[page_n]
        return (*page._pt2pixel(bbox[0], bbox[3]), *page._pt2pixel(bbox[2], bbox[1]))

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
    padding: 0% 1.5em;
}
        '''
        css_rel_path = pjoin('resources', 'stylesheet.css')
        css_filename = pjoin(self.paper.output_dir, css_rel_path)
        with open(css_filename, 'w', encoding="utf-8_sig") as f:
            f.write(css_content)

        return self._export_zoomed_htmls(css_rel_path)
