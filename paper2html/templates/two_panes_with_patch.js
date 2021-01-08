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
