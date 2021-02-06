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


class BBox:
    def __init__(self, raw_bbox, orig='LT'):
        self.orig = orig
        if orig == 'LT':
            self.left = raw_bbox[0]
            self.top = raw_bbox[1]
            self.right = raw_bbox[2]
            self.bottom = raw_bbox[3]
        elif orig == 'LB':
            self.left = raw_bbox[0]
            self.bottom = raw_bbox[1]
            self.right = raw_bbox[2]
            self.top = raw_bbox[3]
        else:
            raise NotImplementedError

    @property
    def width(self):
        return abs(self.right - self.left)

    @property
    def height(self):
        return abs(self.bottom - self.top)

    def unify(self, other):
        if self.orig != other.orig:
            raise ValueError(f"origin is not the same. {self.orig} vs {other.orig}")
        if self.orig == 'LT':
            left = min(self.left, other.left)
            top = min(self.top, other.top)
            right = max(self.right, other.right)
            bottom = max(self.bottom, other.bottom)
            return BBox([left, top, right, bottom], orig='LT')
        if self.orig == 'LB':
            left = min(self.left, other.left)
            bottom = min(self.bottom, other.bottom)
            right = max(self.right, other.right)
            top = max(self.top, other.top)
            return BBox([left, bottom, right, top], orig='LB')
        raise NotImplementedError

    @staticmethod
    def unify_bboxes(bboxes):
        assert len(bboxes) > 0
        bbox = BBox([math.inf, math.inf, -math.inf, -math.inf], orig=bboxes[0].orig)
        for item in bboxes:
            bbox = bbox.unify(item)
        return bbox

    def inflate(self, d):
        if self.orig == 'LB':
            return BBox([self.left - d, self.bottom - d, self.right + d, self.top + d], orig='LB')
        if self.orig == 'LT':
            return BBox([self.left - d, self.top - d, self.right + d, self.bottom + d], orig='LT')
        raise NotImplementedError

    @staticmethod
    def center_dist(bbox1, bbox2):
        x1 = bbox1.left + bbox1.right
        y1 = bbox1.bottom + bbox1.top
        x2 = bbox2.left + bbox2.right
        y2 = bbox2.bottom + bbox2.top
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)/2.

    @staticmethod
    def collided(bbox0, bbox1):
        if bbox0.orig != bbox1.orig:
            raise ValueError(f"origin is not the same. {bbox0.orig} vs {bbox1.orig}")
        if bbox0.orig == 'LT':
            bbox0_ = (bbox0.left, bbox0.top, bbox0.right, bbox0.bottom)
            bbox1_ = (bbox1.left, bbox1.top, bbox1.right, bbox1.bottom)
        elif bbox0.orig == 'LB':
            bbox0_ = (bbox0.left, bbox0.bottom, bbox0.right, bbox0.top)
            bbox1_ = (bbox1.left, bbox1.bottom, bbox1.right, bbox1.top)
        else:
            raise NotImplementedError

        def collided_in_plane(bbox0, bbox1, offset):
            my_head_elm = bbox0[offset]
            my_tail_elm = bbox0[offset + 2]
            other_head_elm = bbox1[offset]
            other_tail_elm = bbox1[offset + 2]
            collided = abs((my_head_elm + my_tail_elm) - (other_head_elm + other_tail_elm)) <= \
                       (my_tail_elm - my_head_elm) + (other_tail_elm - other_head_elm)
            return collided
        return all(collided_in_plane(bbox0_, bbox1_, offset) for offset in [0, 1])


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
    def __init__(self, page_n, bbox, text, item_type, separated=False):
        bbox_ = bbox
        if bbox.right - bbox.left < 0 or bbox.top - bbox.bottom < 0:
            # 幅0でclipするとエラーなので膨らませておく
            bbox_ = BBox((0, 0, 1, 1), orig='LB')
        self.bbox = bbox_
        self.page_n = page_n
        self.text = text
        self.type = item_type
        self.separated = separated
        self.url = None
        self.address = None


@has_global_id
class Paragraph:
    """
    １つの段落単位を表す．（PaperItemの段落は1ページに収まる段落の一部）
    段落だけでなく，図やセクションヘッダも１つの段落単位とする．
    """
    def __init__(self, paper_items):
        self.paper_items = paper_items

    def append(self, paper_item):
        self.paper_items.append(paper_item)

    def extend(self, paragraph):
        self.paper_items.extend(paragraph.paper_items)

    def __getitem__(self, item):
        return self.paper_items[item]

    def __len__(self):
        return len(self.paper_items)


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

        self.image = None

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
        # entry: (address, -top, left, paper_item)
        self.sorted_items = sorted(self.sorted_items, key=lambda entry: entry[:-1])

    def _detect_center_line(self, page_bbox):
        # TODO: センターラインの検出を行う
        center_x = 0.52 * page_bbox.left + 0.48 * page_bbox.right
        return center_x

    def _address_items(self):
        # 2段組みだと仮定する
        page_bbox = self.bbox
        center_x = self._detect_center_line(page_bbox)
        left_side, right_side = (center_x, center_x)
        bottom_side, top_side = (page_bbox.bottom, page_bbox.top)
        # 上と下から順に(目を閉じるような順で)itemを見て，centerlineを超える上下のitemでheader,footer領域を決定する
        eye_closing_ordered = sorted(
            self.items, key=lambda item: min(item.bbox.bottom - page_bbox.bottom,
                                             page_bbox.top - item.bbox.top))
        for item in eye_closing_ordered:
            if item.type == PaperItemType.VTextBox:
                continue
            bbox = item.bbox
            left_side = min(left_side, bbox.left)
            right_side = max(right_side, bbox.right)
            if bbox.left < center_x < bbox.right:
                if abs(bbox.bottom - bottom_side) > abs(top_side - bbox.top):
                    top_side = min(top_side, bbox.bottom)
                else:
                    bottom_side = max(bottom_side, bbox.top)

        self.header_bbox = BBox((left_side, top_side, right_side, page_bbox.top), orig='LB')
        self.left_bbox = BBox((left_side, bottom_side + 1, center_x, top_side - 1), orig='LB')
        self.right_bbox = BBox((center_x, bottom_side + 1, right_side, top_side - 1), orig='LB')
        self.footer_bbox = BBox((left_side, page_bbox.bottom, right_side, bottom_side), orig='LB')

        for item in self.items:
            bbox = item.bbox
            if BBox.collided(bbox, self.header_bbox):
                page_address = PageAddress.Head
            elif BBox.collided(bbox, self.left_bbox):
                page_address = PageAddress.Left
            elif BBox.collided(bbox, self.right_bbox):
                page_address = PageAddress.Right
            elif BBox.collided(bbox, self.footer_bbox):
                page_address = PageAddress.Foot
            else:
                page_address = PageAddress.Etc
            item.address = page_address
            self.sorted_items.append((page_address, -bbox.top, bbox.left, item))
        # 1段組みの場合
        if len([item for addr, _, _, item in self.sorted_items
                if addr == PageAddress.Left or addr == PageAddress.Right]) == 0:
            self.header_bbox = BBox((left_side, page_bbox.top, right_side, page_bbox.top), orig='LB')
            self.left_bbox = BBox((left_side, page_bbox.bottom + 1, right_side - 1, page_bbox.top - 1), orig='LB')
            self.right_bbox = BBox((right_side, page_bbox.bottom + 1, right_side, page_bbox.top - 1), orig='LB')
            self.footer_bbox = BBox((left_side, page_bbox.bottom, right_side, page_bbox.bottom), orig='LB')
            for i in range(len(self.sorted_items)):
                self.sorted_items[i][-1].address = PageAddress.Left
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
            unified.address = addr
            unified_items.append((addr, -unified.bbox.top, unified.bbox.left, unified))
            # for used_item in overlaps:
            #     self.sorted_items.remove((addr, -used_item.bbox.top, used_item.bbox.left, used_item))
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
                unified_bbox = unified_bbox.unify(other.bbox)
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
                unified_bbox = unified_bbox.unify(other.bbox)
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
        for item in sorted(overlaps, key=lambda i: -i.bbox.top):
            if item.type in content_types:
                texts.append(item.text)
            if item.type == PaperItemType.TextBox or item.type == PaperItemType.Paragraph:
                if first_paragraph:
                    first_paragraph = False
                    separated = item.separated
        text = ''.join(texts)
        # 統合が終わったあとに最小限のbboxに整形する
        # TODO: 数式の一部が切れる
        bbox = BBox.unify_bboxes([item.bbox for item in overlaps])
        result = PaperItem(self.page_n, bbox, text, PaperItemType.Paragraph, separated)
        return result

    def _get_inflated_bbox(self, bbox, address):
        # 幅いっぱいにbboxを拡大する
        result = BBox((bbox.left, bbox.bottom, bbox.right, bbox.top), orig='LB')
        frame_bbox = self.address_bbox(address)
        result.left = frame_bbox.left
        result.right = frame_bbox.right
        return result

    def _overlaps_collided(self, overlaps, bbox, item, line_margin):
        # TODO: カラム外の縦書きテキストを構成から分離する
        if item.type == PaperItemType.VTextBox:
            return False
        if not self._range_collided(bbox.bottom, bbox.top, item.bbox.bottom - line_margin, item.bbox.top + line_margin):
            return False
        if self._range_collided(bbox.bottom, bbox.top, item.bbox.bottom, item.bbox.top):
            return True
        # LTLineなどに対してはline_marginを使用しない．textbox間でのみ使用する
        nearest_item = sorted(overlaps, key=lambda i: BBox.center_dist(i.bbox, item.bbox))[0]
        return not self._is_split_type(nearest_item.type) and self._is_split_type(item.type)

    @staticmethod
    def _range_collided(a, b, c, d):
        return abs(a + b - c - d) < abs(b - a) + abs(d - c)

    @staticmethod
    def _is_split_type(item_type):
        split_type = {PaperItemType.Figure, PaperItemType.Part_of_Object,
                      PaperItemType.Shape, PaperItemType.Splitter}
        return item_type in split_type

    def _recognize_items(self):
        self.image = Image.open(pjoin(self.image_dir, sorted(os.listdir(self.image_dir))[self.page_n]))
        items_count = len(self.sorted_items)
        i = 0
        while i < items_count:
            address, _, _, item = self.sorted_items[i]
            filename = self._crop_image(item.bbox)
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
                        if composed_bbox.bottom >= composed_bbox.top:
                            item.type = PaperItemType.Paragraph
                            i += 1
                            continue
                        new_item = PaperItem(self.page_n, composed_bbox, " ", PaperItemType.Paragraph)
                        filename = self._crop_image(new_item.bbox)
                        new_item.url = filename
                        collapsed_texts = []
                        for item_ in self._collided_items(new_item.bbox):
                            item_.type = PaperItemType.Part_of_Object
                            collapsed_texts.append(item_.text)
                        new_item.text = re.sub(r"\n", "", "".join(collapsed_texts)) + "\n"
                        new_item.address = address
                        self.sorted_items.insert(i, (address, -composed_bbox.top, composed_bbox.left, new_item))
                        items_count += 1
                else:
                    item.type = PaperItemType.Paragraph
            i += 1

    def _collided_items(self, bbox):
        return (item for _, _, _, item in self.sorted_items if BBox.collided(item.bbox, bbox))

    def _pt2pixel(self, x, y):
        """
        x, yの原点はpdfと同じLBであることを仮定
        """
        assert self.bbox.orig == 'LB'
        xsize, ysize = self.image.size
        xrate = (x - self.bbox.left) / self.bbox.width
        yrate = (self.bbox.top - y) / self.bbox.height
        return int(xsize * xrate), int(ysize * yrate)

    def _crop_image(self, bbox):
        assert bbox.orig == 'LB'
        cropbox = (*self._pt2pixel(bbox.left, bbox.top), *self._pt2pixel(bbox.right, bbox.bottom))
        cropped = self.image.crop(cropbox)
        filename = pjoin(self.crop_dir, "item_%d_%d_%d_%d_%d.png" % (self.page_n, bbox.left, bbox.bottom, bbox.right, bbox.top))
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
        width = address_bbox.right - address_bbox.left
        CENTER_RATE = 0.1
        left_centered = (bbox.left - address_bbox.left > CENTER_RATE * width)
        right_centered = (address_bbox.right - bbox.right > CENTER_RATE * width)
        CENTER_RATE = 0.35
        left_centered2 = (bbox.left - address_bbox.left > CENTER_RATE * width)
        right_centered2 = (address_bbox.right - bbox.right > CENTER_RATE * width)
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
                        bound = item.bbox.bottom - 1
                    else:
                        bound = item.bbox.top + 1
                    uncentered = item
                    break
            if not bound:
                if reverse:
                    bound = address_bbox.top - 1
                else:
                    bound = address_bbox.bottom + 1
            return bound, uncentered
        bottom, uncentered_b = get_uncentered_item_bound(i)
        top, uncentered_c = get_uncentered_item_bound(i, reverse=True)
        # assert bottom < top
        return BBox((address_bbox.left, bottom, address_bbox.right, top), orig='LB')

    def _reap_paragraphs(self, target_address, paragraphs):
        # TODO: caption判定がひどい
        caption_continue = False
        paragraph_continue = False
        for address, my, x, item in self.sorted_items:
            if address not in target_address:
                continue
            if item.type == PaperItemType.SectionHeader:
                paragraphs.append(Paragraph([item]))
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
                    paragraphs.append(Paragraph([item]))
                    caption_continue = False
                    paragraph_continue = item.separated
            elif item.type == PaperItemType.Caption:
                self.captions.append(Paragraph([item]))
                caption_continue = item.separated
                paragraph_continue = False
            elif item.type == PaperItemType.Figure:
                self.captions.append(Paragraph([item]))

    def _arrange_paragraphs(self):
        self._reap_paragraphs((PageAddress.Head,), self.headers)
        self._reap_paragraphs((PageAddress.Left, PageAddress.Right), self.body_paragraphs)
        self._reap_paragraphs((PageAddress.Foot,), self.footers)


class Paper:
    """
    pdfminerの解析結果を表すクラス．
    """
    output_dir = None
    layout_dir = None
    # n_div_paragraph = 200
    n_div_paragraph = math.inf

    def __init__(self, line_height, line_margin):
        self.pages = []
        self.line_height = line_height
        self.line_margin = line_margin
        self._paragraphs = None

    def add_page(self, page):
        page.recognize(self.line_height, self.line_margin)
        self.pages.append(page)
        self._paragraphs = None

    @property
    def paragraphs(self):
        """
        段落のリスト．読む順序に合わせて塊ごとに並んでいる．
        @return: list of Paragraph
        """
        if not self._paragraphs:
            self._arrange_paragraphs()
        return self._paragraphs

    def _arrange_paragraphs(self):
        self._paragraphs = []
        body_separated = False
        for page in self.pages:
            # TODO: 小文字から始まる段落を前の段落に結合するべき？（現状は前段落のピリオドを手がかりにしている）
            if body_separated and page.body_paragraphs:
                self._paragraphs[-1].extend(page.body_paragraphs[0])

            self._paragraphs.extend(page.headers)
            self._paragraphs.extend(page.captions)

            offset = 0 if not body_separated else 1
            self._paragraphs.extend(page.body_paragraphs[offset:])
            if page.body_paragraphs:
                body_separated = page.body_paragraphs[-1][-1].separated

            self._paragraphs.extend(page.footers)

    def _draw_rect(self, bbox, ax, ec_str="#000000"):
        import matplotlib.patches as patches
        ax.add_patch(patches.Rectangle(xy=(bbox.left, bbox.bottom),
                                       width=bbox.right - bbox.left, height=bbox.top - bbox.bottom,
                                       ec=ec_str, fill=False))

    def show_layouts(self):
        """
        青枠：論文のカラム構成
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
