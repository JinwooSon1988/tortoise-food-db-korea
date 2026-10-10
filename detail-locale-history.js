/* Keep language switches out of browser back-stack on generated plant pages. */
(function(){
  var nav=document.querySelector('.detailnav .langswitch');
  if(!nav)return;
  nav.addEventListener('click',function(event){
    var link=event.target.closest('a[hreflang]');
    if(!link||!nav.contains(link))return;
    var lang=link.getAttribute('hreflang');
    if(lang!=='ko'&&lang!=='en')return;
    event.preventDefault();
    event.stopImmediatePropagation();
    try{localStorage.setItem('tfdblang',lang)}catch(e){}
    if(link.href!==location.href)location.replace(link.href);
  },true);
})();
