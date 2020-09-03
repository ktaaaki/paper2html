import re
import os
import math
from enum import IntEnum
import inspect
from os.path import join as pjoin
from PIL import Image


def has_global_id(target_cls, name='idx'):
    target_cls.__number_of_all_instances__ = 0
    methods = dict(inspect.getmembers(target_cls))

    def wrapped_init(self, *args, **kwargs):
        setattr(self, name, target_cls.__number_of_all_instances__ + 1)
        target_cls.__number_of_all_instances__ += 1
        methods['__init__'](self, *args, **kwargs)
    setattr(target_cls, '__init__', wrapped_init)
    return target_cls


def format4gt2(txt):
    result = txt
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


def unify_bboxes(bboxes):
    bbox = [math.inf, math.inf, -math.inf, -math.inf]
    for item_bbox in bboxes:
        bbox[0] = min(bbox[0], item_bbox[0])
        bbox[1] = min(bbox[1], item_bbox[1])
        bbox[2] = max(bbox[2], item_bbox[2])
        bbox[3] = max(bbox[3], item_bbox[3])
    return bbox


class PageAddress(IntEnum):
    Head = 0
    Left = 1
    Right = 2
    Foot = 3
    Etc = 4


class PaperItemType(IntEnum):
    TextBox = 0
    VTextBox = 1
    Shape = 2
    Figure = 3
    Char = 9

    Paragraph = 4
    SectionHeader = 5
    Caption = 6
    Splitter = 7
    Part_of_Object = 8


@has_global_id
class PaperItem:
    def __init__(self, bbox, text, item_type, separated=False):
        bbox_ = bbox
        if bbox[2] - bbox[0] < 0 or bbox[3] - bbox[1] < 0:
            # 幅0でclipするとエラーなので膨らませておく
            bbox_ = (0, 0, 1, 1)
        self.bbox = bbox_
        self.text = text
        self.type = item_type
        self.separated = separated
        self.url = None


@has_global_id
class PaperPage:
    # TODO: 変数管理を改善する
    image_dir = None
    crop_dir = None

    def __init__(self, bbox, page_n):
        self.bbox = bbox
        self.items = []
        self.page_n = page_n

        self.header_bbox = None
        self.left_bbox = None
        self.right_bbox = None
        self.footer_bbox = None
        self.sorted_items = []

        self.headers = []
        self.footers = []
        self.body_paragraphs = []
        self.captions = []

    def recognize(self, line_height, line_margin):
        """
        pdfminerから読み取られた描画オブジェクトを論文形式の文書として認識する
        """
        self._address_items()
        self._sort_items()
        self._unify_items(line_margin)
        self._sort_items()
        self._recognize_items()
        self._sort_items()
        self._arrange_paragraphs()

    def _sort_items(self):
        self.sorted_items = sorted(self.sorted_items, key=lambda entry: entry[:-1])

    def _address_items(self):
        # 2段組みだと仮定する
        page_bbox = self.bbox
        # TODO: 多段組の行頭検出をソフトにする
        center_x = (page_bbox[0] + page_bbox[2]) / 2.
        min_x, max_x = (center_x, center_x)
        min_y, max_y = (page_bbox[1], page_bbox[3])
        # 上と下から順に(目を閉じるような順で)itemを見て，centerlineを超える上下のitemでheader,footer領域を決定する
        eye_closing_ordered = sorted(self.items, key=lambda item:
        min(item.bbox[1] - page_bbox[1],
            page_bbox[3] - item.bbox[3]))
        for item in eye_closing_ordered:
            if item.type == PaperItemType.VTextBox:
                continue
            bbox = item.bbox
            min_x = min(min_x, bbox[0])
            max_x = max(max_x, bbox[2])
            if bbox[0] < center_x < bbox[2]:
                if abs(bbox[1] - min_y) > abs(max_y - bbox[3]):
                    max_y = min(max_y, bbox[1])
                else:
                    min_y = max(min_y, bbox[3])

        self.header_bbox = (min_x, max_y, max_x, page_bbox[3])
        self.left_bbox = (min_x, min_y + 1, center_x, max_y - 1)
        self.right_bbox = (center_x, min_y + 1, max_x, max_y - 1)
        self.footer_bbox = (min_x, page_bbox[1], max_x, min_y)

        for item in self.items:
            bbox = item.bbox
            if self._collided(bbox, self.header_bbox):
                page_address = PageAddress.Head
            elif self._collided(bbox, self.left_bbox):
                page_address = PageAddress.Left
            elif self._collided(bbox, self.right_bbox):
                page_address = PageAddress.Right
            elif self._collided(bbox, self.footer_bbox):
                page_address = PageAddress.Foot
            else:
                page_address = PageAddress.Etc
            self.sorted_items.append((page_address, -bbox[3], bbox[0], item))
        # 1段組みの場合
        if len([item for addr, _, _, item in self.sorted_items
                if addr == PageAddress.Left or addr == PageAddress.Right]) == 0:
            self.header_bbox = (min_x, page_bbox[3], max_x, page_bbox[3])
            self.left_bbox = (min_x, page_bbox[1] + 1, max_x - 1, page_bbox[3] - 1)
            self.right_bbox = (max_x, page_bbox[1] + 1, max_x, page_bbox[3] - 1)
            self.footer_bbox = (min_x, page_bbox[1], max_x, page_bbox[1])
            for i in range(len(self.sorted_items)):
                self.sorted_items[i] = (PageAddress.Left, *self.sorted_items[i][1:])
            # TODO: ページフッターを認識して段落間から除去する
            # 上下のラインを検出したいところ（なければheader, footerはない，ともいいきれない)

    def address_bbox(self, address):
        if address == PageAddress.Head:
            return self.header_bbox
        if address == PageAddress.Left:
            return self.left_bbox
        if address == PageAddress.Right:
            return self.right_bbox
        if address == PageAddress.Foot:
            return self.footer_bbox
        else:
            raise ValueError()

    def _unify_items(self, line_margin):
        unified_items = []
        while len(self.sorted_items) != 0:
            addr, mb3, b0, item = self.sorted_items.pop(0)
            overlaps = self._pop_overlaps(item, addr, line_margin)
            unified = self._make_unified(overlaps)
            unified_items.append((addr, -unified.bbox[3], unified.bbox[0], unified))
            # for used_item in overlaps:
            #     self.sorted_items.remove((addr, -used_item.bbox[3], used_item.bbox[0], used_item))
        self.sorted_items = unified_items

    def _pop_overlaps(self, item, address, line_margin):
        unified_bbox = item.bbox
        overlaps = [item]
        remove_ids = []
        for i in range(len(self.sorted_items)):
            other_addr, _, _, other = self.sorted_items[i]
            if other_addr != address:
                continue
            if self._overlaps_collided(overlaps, unified_bbox, other, line_margin):
                overlaps.append(other)
                unified_bbox = unify_bboxes((unified_bbox, other.bbox))
                remove_ids.insert(0, i)
        for i in remove_ids:
            self.sorted_items.pop(i)

        remove_ids = []
        for i in range(len(self.sorted_items) - 1, -1, -1):
            other_addr, _, _, other = self.sorted_items[i]
            if other_addr != address or other in overlaps:
                continue
            if self._overlaps_collided(overlaps, unified_bbox, other, line_margin):
                overlaps.append(other)
                unified_bbox = unify_bboxes((unified_bbox, other.bbox))
                remove_ids.append(i)
        for i in remove_ids:
            self.sorted_items.pop(i)
        return overlaps

    def _make_unified(self, overlaps):
        # TODO: 一つだけの出力になるか確かめる
        separated = False
        first_paragraph = True
        content_types = {PaperItemType.Paragraph, PaperItemType.SectionHeader,
                         PaperItemType.TextBox, PaperItemType.Caption,
                         PaperItemType.Char, PaperItemType.VTextBox}
        texts = []
        for item in sorted(overlaps, key=lambda i: -i.bbox[3]):
            if item.type in content_types:
                texts.append(item.text)
            if item.type == PaperItemType.TextBox or item.type == PaperItemType.Paragraph:
                if first_paragraph:
                    first_paragraph = False
                    separated = item.separated
        text = ''.join(texts)
        # 統合が終わったあとに最小限のbboxに整形する
        # TODO: 数式の一部が切れる
        bbox = unify_bboxes(item.bbox for item in overlaps)
        result = PaperItem(bbox, text, PaperItemType.Paragraph, separated)
        return result

    def _get_inflated_bbox(self, bbox, address):
        # 幅いっぱいにbboxを拡大する
        result = [*bbox]
        frame_bbox = self.address_bbox(address)
        result[0] = frame_bbox[0]
        result[2] = frame_bbox[2]
        return result

    def _overlaps_collided(self, overlaps, bbox, item, line_margin):
        # TODO: カラム外の縦書きテキストを構成から分離する
        if item.type == PaperItemType.VTextBox:
            return False
        if not self._range_collided(bbox[1], bbox[3], item.bbox[1] - line_margin, item.bbox[3] + line_margin):
            return False
        if self._range_collided(bbox[1], bbox[3], item.bbox[1], item.bbox[3]):
            return True
        # LTLineなどに対してはline_marginを使用しない．textbox間でのみ使用する
        nearest_item = sorted(overlaps, key=lambda i: self._bbox_dist(i.bbox, item.bbox))[0]
        return not self._is_split_type(nearest_item.type) and self._is_split_type(item.type)

    @staticmethod
    def _range_collided(a, b, c, d):
        return abs(a + b - c - d) < abs(b - a) + abs(d - c)

    @staticmethod
    def _bbox_dist(bbox1, bbox2):
        x1 = bbox1[0] + bbox1[2]
        y1 = bbox1[1] + bbox1[3]
        x2 = bbox2[0] + bbox2[2]
        y2 = bbox2[1] + bbox2[3]
        return (x1 - x2) ** 2 + (y1 - y2) ** 2

    @staticmethod
    def _is_split_type(item_type):
        split_type = {PaperItemType.Figure, PaperItemType.Part_of_Object,
                      PaperItemType.Shape, PaperItemType.Splitter}
        return item_type in split_type

    def _recognize_items(self):
        image = Image.open(pjoin(self.image_dir, sorted(os.listdir(self.image_dir))[self.page_n]))
        items_count = len(self.sorted_items)
        i = 0
        while i < items_count:
            address, _, _, item = self.sorted_items[i]
            filename = self._crop_image(image, item.bbox)
            item.url = filename
            if item.type == PaperItemType.TextBox:
                if self._is_section_header(item.text):
                    item.type = PaperItemType.SectionHeader
                elif self._is_caption(item.text):
                    item.type = PaperItemType.Caption
                elif self._is_separated_paragraph(item, address):
                    item.type = PaperItemType.SeparatedParagraph
                # TODO: 数式のような中央揃えの行を検出して，すべての領域を_get_composed_bboxで発見しているが，もはや不要
                elif self._is_centered(item.bbox, self.address_bbox(address), item.text):
                    if any(not self._is_centered(item_.bbox, self.address_bbox(address), item_.text)
                           for item_ in self._collided_items(item.bbox)):
                        item.type = PaperItemType.Part_of_Object
                    else:
                        composed_bbox = self._get_composed_bbox(i, address, self.address_bbox(address))
                        if composed_bbox[1] >= composed_bbox[3]:
                            item.type = PaperItemType.Paragraph
                            i += 1
                            continue
                        new_item = PaperItem(composed_bbox, " ", PaperItemType.Paragraph)
                        filename = self._crop_image(image, new_item.bbox)
                        new_item.url = filename
                        collapsed_texts = []
                        for item_ in self._collided_items(new_item.bbox):
                            item_.type = PaperItemType.Part_of_Object
                            collapsed_texts.append(item_.text)
                        new_item.text = re.sub(r"\n", "", "".join(collapsed_texts)) + "\n"
                        self.sorted_items.insert(i, (address, -composed_bbox[3], composed_bbox[0], new_item))
                        items_count += 1
                else:
                    item.type = PaperItemType.Paragraph
            i += 1

    def _collided_items(self, bbox):
        return (item for _, _, _, item in self.sorted_items if self._collided(item.bbox, bbox))

    def _pt2pixel(self, x, y, image):
        xsize, ysize = image.size
        xrate, yrate = (xsize / (self.bbox[2] - self.bbox[0]), ysize / (self.bbox[3] - self.bbox[1]))
        return int((x - self.bbox[0]) * xrate), int((self.bbox[3] - y) * yrate)

    def _crop_image(self, image, bbox):
        cropbox = (*self._pt2pixel(bbox[0], bbox[3], image), *self._pt2pixel(bbox[2], bbox[1], image))
        cropped = image.crop(cropbox)
        filename = pjoin(self.crop_dir, "item_%d_%d_%d_%d_%d.jpg" % (self.page_n, bbox[0], bbox[1], bbox[2], bbox[3]))
        if cropped.width == 0 or cropped.height == 0:
            cropped = Image.new('RGB', (1, 1), (0xdd, 0xdd, 0xdd))
        cropped.save(filename)
        return filename

    def _is_one_line(self, text):
        return len(text.split('\n')) == 1

    def _is_section_header(self, text):
        # タイトルは章番号でおおよそ分かる，太字などの情報もあるといいかもしれない
        text_s = text.strip()
        if text_s == "Abstract" or text_s == "References":
            return True
        head_line = text.split('\n')[0]
        split_head_line = head_line.split(' ')
        if len(split_head_line) < 2:
            return False
        header, title = (split_head_line[0], split_head_line[1])
        # print(title)
        if len(header) == 0 or header[-1] != ".":
            return False
        digits = header.split('.')
        return all(digit.isdigit() for digit in digits)

    def _is_caption(self, text):
        label = text.split('.')[0]
        spl = label.split(' ')
        if len(spl) < 2:
            return False
        label_name, label_id = (spl[0], spl[1])
        if not label_id.isdigit():
            return False
        if label_name == "Figure":
            return True
        elif label_name == "Table":
            return True
        else:
            print("new label name?: " + label_name)

    def _is_separated_paragraph(self, text_box, address):
        # 続きのある段落は，複数行の場合，末尾の空白の有無でわかる．
        # 単一行の場合，領域の90%の幅を占め，タイトルでないかから判定する
        # if not self._is_one_line(text_box.text):
        #     return text_box.separated
        # else:
        #     if address == PageAddress.Left:
        #         space_bbox = self.left_bbox
        #     elif address == PageAddress.Right:
        #         space_bbox = self.right_bbox
        #     else:
        #         return text_box.separated
        #     if self._is_section_header(text_box.text):
        #         return False
        return text_box.separated

    def _is_splitter(self, item, address_bbox):
        # TODO: 下の方かつ一番下かつLTLine
        if item.type != PaperItemType.Shape:
            return False
        pass

    def _contain_math_char(self, text):
        return re.search(r"[\(|\)|=|-|+]", text)

    def _is_centered(self, bbox, address_bbox, text):
        """
        数式の文字断片を見つけるヒューリスティック判定
        """
        if not text:
            return True
        width = address_bbox[2] - address_bbox[0]
        CENTER_RATE = 0.1
        left_centered = (bbox[0] - address_bbox[0] > CENTER_RATE * width)
        right_centered = (address_bbox[2] - bbox[2] > CENTER_RATE * width)
        CENTER_RATE = 0.35
        left_centered2 = (bbox[0] - address_bbox[0] > CENTER_RATE * width)
        right_centered2 = (address_bbox[2] - bbox[2] > CENTER_RATE * width)
        has_short_line = any(len(line) < 16 for line in text.split('\n')[:-1])
        # 16文字以上の行が3行以上ある
        has_long_lines = (sum(1 for line in text.split('\n') if len(line) >= 16) >= 3)
        has_short_line = has_short_line and not has_long_lines
        single_line = (len(text.split('\n')) <= 3)
        contain_math_char = self._contain_math_char(text)
        # word_rate = len(re.findall(r"[a-z|A-Z]", text)) / len(text)
        # if word_rate > 0.5:
        #     return False
        # 大きく右か左にズレているか，少し中央に寄せてあって3行以内か，少し片側に寄せてあって（3行以内数式文字ありか，16文字以内で終わる行がある）
        return any([left_centered2, right_centered2, (left_centered and right_centered and single_line),
                    (left_centered or right_centered) and (has_short_line or single_line and contain_math_char)])

    def _get_composed_bbox(self, i, address, address_bbox):
        """
        ソートされたアイテムの上下関係から余白を含めた矩形全体を取得する
        """
        def get_uncentered_item_bound(i_start, reverse=False):
            bound = None
            uncentered = None
            if reverse:
                searching_items = reversed(self.sorted_items[:i_start])
            else:
                searching_items = self.sorted_items[i_start+1:]
            for item_addr, _, _, item in searching_items:
                if item_addr != address:
                    break
                is_other_type = any((self._is_section_header(item.text),
                                     self._is_caption(item.text),
                                     self._is_separated_paragraph(item, item_addr)))
                if is_other_type or not self._is_centered(item.bbox, address_bbox, item.text):
                    if reverse:
                        bound = item.bbox[1] - 1
                    else:
                        bound = item.bbox[3] + 1
                    uncentered = item
                    break
            if not bound:
                if reverse:
                    bound = address_bbox[3] - 1
                else:
                    bound = address_bbox[1] + 1
            return bound, uncentered
        bottom, uncentered_b = get_uncentered_item_bound(i)
        top, uncentered_c = get_uncentered_item_bound(i, reverse=True)
        # assert bottom < top
        return address_bbox[0], bottom, address_bbox[2], top

    def _reap_paragraphs(self, target_address, paragraphs):
        # TODO: caption判定がひどい
        caption_continue = False
        paragraph_continue = False
        for address, my, x, item in self.sorted_items:
            if address not in target_address:
                continue
            if item.type == PaperItemType.SectionHeader:
                paragraphs.append([item])
                caption_continue = False
                paragraph_continue = False
            elif item.type == PaperItemType.Paragraph:
                if caption_continue:
                    self.captions[-1].append(item)
                    caption_continue = item.separated
                    paragraph_continue = False
                elif paragraph_continue:
                    paragraphs[-1].append(item)
                    caption_continue = False
                    paragraph_continue = item.separated
                else:
                    paragraphs.append([item])
                    caption_continue = False
                    paragraph_continue = item.separated
            elif item.type == PaperItemType.Caption:
                self.captions.append([item])
                caption_continue = item.separated
                paragraph_continue = False
            elif item.type == PaperItemType.Figure:
                self.captions.append([item])

    def _arrange_paragraphs(self):
        self._reap_paragraphs((PageAddress.Head,), self.headers)
        self._reap_paragraphs((PageAddress.Left, PageAddress.Right), self.body_paragraphs)
        self._reap_paragraphs((PageAddress.Foot,), self.footers)

    @staticmethod
    def _collided(bbox0, bbox1):
        def collided_in_plane(bbox0, bbox1, offset):
            my_head_elm = bbox0[offset]
            my_tail_elm = bbox0[offset + 2]
            other_head_elm = bbox1[offset]
            other_tail_elm = bbox1[offset + 2]
            collided = abs((my_head_elm + my_tail_elm) - (other_head_elm + other_tail_elm)) <= \
                       (my_tail_elm - my_head_elm) + (other_tail_elm - other_head_elm)
            return collided
        return all(collided_in_plane(bbox0, bbox1, offset) for offset in [0, 1])


class Paper:
    """
    pdfminerの解析結果を表すクラス．
    """
    output_dir = None
    layout_dir = None
    n_div_paragraph = 200

    def __init__(self, line_height, line_margin):
        self.pages = []
        self.arranged_paragraphs = None
        self.line_height = line_height
        self.line_margin = line_margin

    def add_page(self, page):
        page.recognize(self.line_height, self.line_margin)
        self.pages.append(page)
        self.arranged_paragraphs = None

    def _arrange_paragraphs(self):
        self.arranged_paragraphs = []
        body_separated = False
        for page in self.pages:
            # TODO: 小文字から始まる段落を前の段落に結合するべき？（現状は前段落のピリオドを手がかりにしている）
            if body_separated and page.body_paragraphs:
                self.arranged_paragraphs[-1].extend(page.body_paragraphs[0])

            self.arranged_paragraphs.extend(page.headers)
            self.arranged_paragraphs.extend(page.captions)

            offset = 0 if not body_separated else 1
            self.arranged_paragraphs.extend(page.body_paragraphs[offset:])
            if page.body_paragraphs:
                body_separated = page.body_paragraphs[-1][-1].separated

            self.arranged_paragraphs.extend(page.footers)

    def _paragraph2txt(self, paragraph):
        eng_txt = format4gt2("".join([item.text for item in paragraph]))
        return eng_txt

    def get_text(self):
        if not self.arranged_paragraphs:
            self._arrange_paragraphs()
        result = "".join([self._paragraph2txt(paragraph) for paragraph in self.arranged_paragraphs])
        return result

    def _paragraph2markdown(self, paragraph):
        if len(paragraph) == 0:
            return ""
        if paragraph[0].type == PaperItemType.SectionHeader:
            return "## " + self._paragraph2txt(paragraph)
        elif paragraph[0].type == PaperItemType.Figure:
            return "![Figure](file://%s)\n" % os.path.abspath(paragraph[0].url)
        else:
            return "\n".join([
                                 "![Figure](file://%s)\n" % os.path.abspath(item.url) for item in paragraph
                             ] + [self._paragraph2txt(paragraph)])

    def _paragraph2img_line(self, paragraph, i):
        img_template = '<p id="img{}"><img alt="Figure" src="file://{}" /></p>\n'
        if paragraph[0].type == PaperItemType.Figure:
            return img_template.format(i, os.path.abspath(paragraph[0].url))
        else:
            return "\n".join([img_template.format(i, os.path.abspath(item.url)) for item in paragraph])

    def _paragraph2txt_line(self, paragraph, i):
        txt_template = '<p id="txt{}">{}</p>\n'
        if len(paragraph) == 0:
            return ""
        if paragraph[0].type == PaperItemType.SectionHeader:
            return '<h2 id="txt{}">{}</h2>\n'.format(i, self._paragraph2txt(paragraph))
        elif paragraph[0].type == PaperItemType.Figure:
            return txt_template.format(i, "")
        else:
            return txt_template.format(i, self._paragraph2txt(paragraph))

    def get_htmls(self, pdf_name):
        if not self.arranged_paragraphs:
            self._arrange_paragraphs()

        def chunks(list, n):
            for i in range(0, len(list), n):
                yield list[i:i + n]
        javascript = '''
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
                  leftw.scrollTo(img_line.offsetLeft, img_line.offsetTop + delta_ - center_);
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
        for paragraphs in chunks(self.arranged_paragraphs, self.n_div_paragraph):
            img_content = "\n\n\n\n\n".join([self._paragraph2img_line(paragraph, i) for i, paragraph in enumerate(paragraphs)])
            txt_content = "\n\n\n\n\n".join([self._paragraph2txt_line(paragraph, i) for i, paragraph in enumerate(paragraphs)])

            html_pages.append([img_content, txt_content])
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
        css_filename = pjoin(self.output_dir, 'stylesheet.css')
        with open(css_filename, 'w') as f:
            f.write(css_content)
        html_files = []
        for i, page in enumerate(html_pages):
            top_html_template = '''
                <!DOCTYPE html>
                <html lang="en">
                  <head>
                    <meta http-equiv="Content-type" content="text/html;charset=utf-8" />
                    <link href="stylesheet.css" rel="stylesheet" type="text/css" />
                    <title>
                      {}
                    </title>
                  </head>
                  <body>
                    <div id="split">
                      <header style="position: fixed;">
                        <input type="button" value="30%" onclick="Zoom(0.33);"/>
                        <input type="button" value="50%" onclick="Zoom(0.5);"/>
                        <input type="button" value="75%" onclick="Zoom(0.75);"/>
                        <input type="button" value="100%" onclick="Zoom(1);"/><br />
                      </header><br /><br />
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
            img_c, txt_c = page

            output_filename = pdf_name + '_%d.html' % i
            output_path = pjoin(self.output_dir, output_filename)
            with open(output_path, 'w') as f:
                f.write(top_html_template.format(pdf_name, img_c, txt_c, javascript))
            html_files.append(output_path)
        return html_files

    def _draw_rect(self, bbox, ax, ec_str="#000000"):
        import matplotlib.patches as patches
        ax.add_patch(patches.Rectangle(xy=(bbox[0], bbox[1]),
                                       width=bbox[2] - bbox[0], height=bbox[3] - bbox[1],
                                       ec=ec_str, fill=False))

    def show_layouts(self):
        """
        青枠：カラム構成
        黒枠：テキストボックス
        赤枠：その他
        """
        import matplotlib.pyplot as plt
        plt.figure()
        for page_n, page in enumerate(self.pages):
            ax = plt.axes()
            for item in page.items:
                bbox = item.bbox
                ec_str = "#000000" if item.type == PaperItemType.Paragraph else "#FF0000"
                self._draw_rect(bbox, ax, ec_str)
            for bbox in (page.header_bbox, page.left_bbox, page.right_bbox, page.footer_bbox):
                self._draw_rect(bbox, ax, "#0000FF")

            plt.axis('scaled')
            ax.set_aspect('equal')
            plt.savefig(pjoin(self.layout_dir, 'pdf2jpn%d.png' % page_n))
            plt.clf()

