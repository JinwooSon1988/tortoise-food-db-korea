/* Shared KR/EN language-switch navigation: preserve a user's current search. */
(()=>{'use strict';
 const input=document.getElementById('searchInput');
 if(!input)return;
 const switches=[...document.querySelectorAll('nav.langswitch a[hreflang]')];
 if(!switches.length)return;
 const initial=new URLSearchParams(location.search).get('q');
 const value=()=>String(input.value||'').trim().slice(0,80);
 function sync(){
   const q=value()||(!input.value?initial:'');
   for(const link of switches){
     const target=new URL(link.href,location.href);
     if(q)target.searchParams.set('q',q);else target.searchParams.delete('q');
     link.href=target.href;
   }
 }
 input.addEventListener('input',sync);
 input.addEventListener('change',sync);
 for(const link of switches)link.addEventListener('pointerdown',sync);
 sync();
})();
