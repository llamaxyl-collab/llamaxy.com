// Sepet tarayicida (localStorage); odeme adimi her zaman "gecici olarak kullanilamiyor" der (Apo 4 Kas 2026)
const K='llx_basket',$=s=>document.querySelector(s);
const get=()=>JSON.parse(localStorage.getItem(K)||'[]'),put=b=>{localStorage.setItem(K,JSON.stringify(b));badge()};
const gbp=n=>'£'+n.toFixed(2);
function badge(){const e=$('#bkn');if(e)e.textContent=get().reduce((n,x)=>n+x.q,0)}
function totals(b){const sub=b.reduce((n,x)=>n+x.p*x.q,0),del=sub>=40||!sub?0:3.99;return{sub,del,tot:sub+del}}
function toast(t){const d=document.createElement('div');d.className='toast';d.textContent=t;document.body.append(d);setTimeout(()=>d.remove(),1800)}
document.addEventListener('click',e=>{const b=e.target.closest('button.buy[data-a]');if(!b)return;
  const s=get(),x=s.find(i=>i.a===b.dataset.a);if(x)x.q++;else s.push({a:b.dataset.a,p:+b.dataset.p,t:b.dataset.t,i:b.dataset.i,q:1});put(s);toast('Added to basket')});
function sumHtml(b){const t=totals(b);return `<div class="sum"><div><span>Subtotal</span><span>${gbp(t.sub)}</span></div><div><span>Delivery</span><span>${t.del?gbp(t.del):'Free'}</span></div><div class="tot"><span>Total (incl. VAT)</span><span>${gbp(t.tot)}</span></div></div>`}
function cart(){const c=$('#cart');if(!c)return;const b=get();
  if(!b.length){c.innerHTML='<p>Your basket is empty. <a href="products.html">Browse products →</a></p>';return}
  c.innerHTML='<table class="cart">'+b.map((x,i)=>`<tr><td><img src="${x.i}" alt=""></td><td>${x.t}</td><td><input type="number" min="0" max="10" value="${x.q}" data-i="${i}"></td><td style="text-align:right;white-space:nowrap">${gbp(x.p*x.q)}</td></tr>`).join('')+'</table>'
    +sumHtml(b)+'<div style="text-align:right;margin-top:16px"><a class="btn" href="checkout.html">Checkout</a></div>';
  c.querySelectorAll('input').forEach(n=>n.onchange=()=>{const s=get(),q=Math.max(0,Math.min(10,parseInt(n.value)||0));if(q)s[n.dataset.i].q=q;else s.splice(n.dataset.i,1);put(s);cart()})}
function checkout(){const f=$('#co');if(!f)return;const b=get();
  if(!b.length){location.href='basket.html';return}
  $('#osum').innerHTML=`<b>${b.reduce((n,x)=>n+x.q,0)} item(s)</b>`+sumHtml(b);
  f.onsubmit=e=>{e.preventDefault();const p=$('#pay');p.disabled=true;p.innerHTML='<span class="spin"></span>Connecting to payment provider…';$('#perr').innerHTML='';
    setTimeout(()=>{p.disabled=false;p.textContent='Try again';
      $('#perr').innerHTML='<div class="err"><b>Payment could not be started.</b><br>Our payment service is temporarily unavailable. You have not been charged and your basket has been saved. Please try again later.</div>'},2600)}}
badge();cart();checkout();
