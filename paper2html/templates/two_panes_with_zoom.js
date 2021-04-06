//paper2html/paper2html/templates/two_panes_with_zoom.js
//This file is licensed under the MIT license (see LICENSE_MIT for details)
//Copyright (C) 2021 ktaaaki

// setup base elements
const rightw = document.getElementById('right');
const leftw = document.getElementById('left');
const split = document.getElementById( 'split' );

let canvas = document.getElementById('canvas');

function fit_canvas(){
 canvas.width = leftw.clientWidth;
 canvas.height = leftw.clientHeight;
 rightw.style.paddingTop = String(rightw.clientHeight*(1./4.))+"px";
 rightw.style.paddingBottom = String(rightw.clientHeight*(3./4.))+"px";
}
fit_canvas();

// load all images
// 直接ファイルリストをスクリプトに埋め込む
const img_pathes = ####;

let paper_imgs = {};
let loaded_img_count = 0;

function on_img_loaded(){
  onscrollR();
}

for(i = 0; i < img_pathes.length; i++){
//  const img = new Image();
  const closure_i = i;
//  img.src = img_pathes[i];
  const img = document.getElementById(img_pathes[i]);
//  img.onload = function(){
      paper_imgs[closure_i] = img;
      loaded_img_count++;
      if(loaded_img_count == img_pathes.length){
        on_img_loaded();
      }
//  }
}

function parse_address(str_addr) {
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

function get_address(elem) {
  return parse_address(elem.getAttribute("data-address"));
}

function get_papers_transform(paper_size, canvas_size, target, center_height, delta_rate){
  const header_height = document.getElementById('header').clientHeight;
  // canvasはheader分座標がズレないので左右で合わせる必要がある
  const canvas_center_height = center_height - header_height;

  // targetは画像pixelの座標系, canvas drawもpixel座標
  const target_left = target[0];
  const target_top = target[1];
  const target_width = target[2];
  const target_height = target[3];

  const pad_rate = 0.05;
  const zoom = canvas_size[0] / ((1 + 2 * pad_rate) * target_width);
  const left = -target_left + pad_rate * target_width;
  const top = -target_top - target_height * delta_rate + canvas_center_height / zoom;
  return [zoom, left, top];
}

function onscroll_between_txt_line(eye_level, delta_rate, txt_line){
  //const img_line = document.getElementById(txt_line.id.replace('txt', 'img'));
  //const delta_ = delta_rate * img_line.offsetHeight;
  //leftw.scrollTo(0, img_line.offsetTop + delta_ - eye_level);
  const addrs = get_address(txt_line);
  const addr = addrs[0];
  //now_addr = addr;
  const paper_img = paper_imgs[addr[0]];
  const trsf = get_papers_transform(
    [paper_img.width, paper_img.height],
    [leftw.clientWidth, leftw.clientHeight],
    [addr[1], addr[2], addr[3]-addr[1], addr[4]-addr[2]],
    eye_level, delta_rate);
  //now_trsf = trsf;
  return [trsf, addr[0]];
}

function blend_trsf(trsf0, trsf1, delta_rate){
  return [(1-delta_rate) * trsf0[0] + delta_rate * trsf1[0],
          (1-delta_rate) * trsf0[1] + delta_rate * trsf1[1],
          (1-delta_rate) * trsf0[2] + delta_rate * trsf1[2]]
}

function draw_paper(c, trsf, page_idx){
  const paper_img = paper_imgs[page_idx];
  canvas.width = paper_img.width*3;
  canvas.height = paper_img.height*3;
  leftw.scrollTo(trsf[0]*(paper_img.width-trsf[1]), trsf[0]*(paper_img.height-trsf[2]));
  c.fillStyle = "rgb(255, 255, 255)";
  c.fillRect(0, 0, canvas.width, canvas.height);
  c.save();
  c.scale(trsf[0], trsf[0]);
  // drawImage(, dx, dy);
  c.drawImage(paper_img, paper_img.width, paper_img.height);
  if(page_idx != 0){
    const prev_page = paper_imgs[page_idx-1];
    c.drawImage(prev_page, paper_img.width, paper_img.height - prev_page.height);
  }
  if(page_idx != paper_imgs.length-1){
    const next_page = paper_imgs[page_idx+1];
    c.drawImage(next_page, paper_img.width, paper_img.height + next_page.height);
  }
  c.restore();

//  c.fillRect(80, 80, 200, 200);
//  c.fillStyle = "rgb(0, 0, 0)";
////  c.fillText("rate: " + delta_rate.toString(), 100, 100);
////  c.fillText("height: " + (addr[4]-addr[2]).toString(), 100, 120);
//  c.fillText("zoom: " + trsf[0].toString(), 100, 140);
//  c.fillText("paper_width: " + paper_img.width.toString(), 100, 160);
//  c.fillText("paper_height: " + paper_img.height.toString(), 100, 180);
//  c.fillText("canvas_w: " + canvas.width.toString(), 100, 200);
//  c.fillText("canvas_h: " + canvas.height.toString(), 100, 220);
//  c.fillText("y: " + trsf[2].toString(), 100, 240);
}

function onscrollR() {
  fit_canvas();
  let c = canvas.getContext('2d');
  const top_ = split.scrollTop;
  const bottom_ = top_ + split.clientHeight;
  const eye_level = (2/3) * top_ + (1/3) * bottom_;

  for(let i = 0; i < rightw.children.length; i++) {
    const txt_line = rightw.children[i];
    const rect = txt_line.getBoundingClientRect();

    // 段落内に目線の高さがある場合
    if (rect.top <= eye_level && eye_level <= rect.bottom) {
      const delta_rate = (eye_level - rect.top) / rect.height;
      let [trsf, page_idx] = onscroll_between_txt_line(eye_level, delta_rate, txt_line);
      draw_paper(c, trsf, page_idx);
      break;
    }

    // 段落より上に目線の高さがある場合
    let prev_line = null;
    let prev_bottom = 0;
    if (i != 0){
      prev_line = rightw.children[i - 1];
      prev_bottom = prev_line.getBoundingClientRect().bottom;
    }
    if (eye_level <= rect.top && (i == 0 || prev_bottom <= eye_level)) {
      let [trsf1, page_idx1] = onscroll_between_txt_line(eye_level, 0, txt_line);
      if (i == 0){
        draw_paper(c, trsf1, page_idx1);
      } else {
        let [trsf0, page_idx0] = onscroll_between_txt_line(eye_level, 1, prev_line);
        const delta_rate = (eye_level - prev_bottom) / (rect.top - prev_bottom);
        draw_paper(c, blend_trsf(trsf0, trsf1, delta_rate), page_idx0);
      }
      break;
    }

    // 段落より下に目線の高さがある場合
    let next_line = null;
    let next_top = 0;
    if (i != rightw.children.length - 1){
      next_line = rightw.children[i + 1];
      next_top = next_line.getBoundingClientRect().top;
    }
    if (rect.bottom <= eye_level && (i == rightw.children.length - 1 || eye_level <= next_top)) {
      let [trsf0, page_idx0] = onscroll_between_txt_line(eye_level, 1, txt_line);
      if (i == rightw.children.length - 1){
        draw_paper(c, trsf0, page_idx0);
      }
      else {
        let [trsf1, page_idx1] = onscroll_between_txt_line(eye_level, 0, next_line);
        const delta_rate = (eye_level - rect.bottom) / (next_top - rect.bottom);
        draw_paper(c, blend_trsf(trsf0, trsf1, delta_rate), page_idx0);
      }
      break;
    }
  }
}

if( rightw.addEventListener ) {
    rightw.addEventListener('scroll', onscrollR, false);
}
