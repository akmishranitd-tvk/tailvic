(()=>{'use strict';
const $=(s)=>document.querySelector(s),$$=(s)=>[...document.querySelectorAll(s)];
const token=$('meta[name="csrf-token"]')?.content;
const preview=Boolean($('meta[name="tailvic-preview"]'));
const cookie=()=>document.cookie.split('; ').find(v=>v.startsWith('tailvic_analytics='))?.split('=')[1];
function track(event){if(preview||cookie()!=='yes')return;const path=location.pathname.startsWith('/booking/')?'/':location.pathname;fetch('/api/events/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:JSON.stringify({event,path}),keepalive:true}).catch(()=>{});}
const menu=$('.menu-toggle');menu?.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Close navigation':'Open navigation');$('#main-nav')?.classList.toggle('open',open);});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu?.getAttribute('aria-expanded')==='true'){menu.click();menu.focus();}});
$$('[data-track]').forEach(a=>a.addEventListener('click',()=>track(a.dataset.track)));
const banner=$('#cookie-banner');if(!preview&&!cookie()&&banner)banner.hidden=false;
$$('[data-cookie]').forEach(b=>b.addEventListener('click',()=>{document.cookie='tailvic_analytics='+b.dataset.cookie+'; Path=/; Max-Age=15552000; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');banner.hidden=true;if(b.dataset.cookie==='yes')track('page_view');}));
$$('[data-cookie-open]').forEach(b=>b.addEventListener('click',()=>{banner.hidden=false;banner.querySelector('button')?.focus();}));
track('page_view');
const storyToggle=$('[data-story-toggle]'),storyMarquee=$('#story-marquee');
if(storyToggle&&storyMarquee){
 const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
 const updateMotion=()=>{storyToggle.hidden=motion.matches;};
 updateMotion();motion.addEventListener('change',updateMotion);
 storyToggle.addEventListener('click',()=>{const paused=storyMarquee.dataset.paused!=='true';storyMarquee.dataset.paused=String(paused);storyToggle.setAttribute('aria-pressed',String(paused));storyToggle.textContent=paused?'Resume stories':'Pause stories';});
}
function filterPet(pet){$$('[data-pet-filter]').forEach(b=>{const on=b.dataset.petFilter===pet;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});$$('#service-grid [data-species]').forEach(card=>{card.hidden=card.dataset.species!==pet&&card.dataset.species!=='both';});}
$$('[data-pet-filter]').forEach(b=>b.addEventListener('click',()=>filterPet(b.dataset.petFilter)));if($('#service-grid'))filterPet('dog');
const service=$('#service-select'),species=$('#species'),size=$('#size-select');
const catalog=$('#service-catalog')?[...$('#service-catalog').content.querySelectorAll('option')]:[];
const sizeGuides=$('#booking-form')?JSON.parse($('#booking-form').dataset.sizeGuides):{};
const savedServices={},savedSizes={};let previousSpecies=species?.value;
function estimate(){if(!service)return;const o=service.selectedOptions[0];const p=o?.dataset.price;$('#service-estimate').textContent=p?new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'}).format(Number(p)/100):'Quote on request';$('#service-duration').textContent=o?.dataset.duration||'';}
function syncSpecies(){
 if(!service||!species||!size)return;
 savedServices[previousSpecies]=service.value;savedSizes[previousSpecies]=size.value;
 const pet=species.value;
 const options=catalog.filter(o=>o.dataset.species===pet||o.dataset.species==='both').map(o=>o.cloneNode(true));
 const preferred=savedServices[pet];
 service.replaceChildren(...options);
 service.value=options.some(o=>o.value===preferred)?preferred:options[0]?.value||'';
 const choices=sizeGuides[pet]||[];
 size.replaceChildren(...choices.map(item=>new Option(item.label,item.value)));
 const preferredSize=savedSizes[pet]||savedSizes[previousSpecies];
 size.value=choices.some(item=>item.value===preferredSize)?preferredSize:choices[choices.length-1]?.value||'';
 size.title=size.selectedOptions[0]?.textContent||'';
 previousSpecies=pet;estimate();
}
size?.addEventListener('change',()=>{size.title=size.selectedOptions[0]?.textContent||'';});
species?.addEventListener('change',syncSpecies);service?.addEventListener('change',estimate);syncSpecies();
$$('input[name="mode"]').forEach(r=>r.addEventListener('change',()=>{const slots=r.value==='slot';$('[data-slot-panel]').hidden=!slots;$('[data-request-panel]').hidden=slots;$('input[name="preferred"]').required=!slots;$$('input[name="slot_id"]').forEach(x=>x.required=slots);}));
if($('#booking-form')){track('booking_start');const p=$('input[name="preferred"]');if(p){const local=new Date(Date.now()+330*60000).toISOString().slice(0,16);p.min=local;}}
$$('[data-confirm]').forEach(b=>b.addEventListener('click',e=>{if(!confirm(b.dataset.confirm))e.preventDefault();}));
$$('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(b.dataset.copy);const t=$('#toast');t.textContent='UPI ID copied';t.classList.add('visible');setTimeout(()=>t.classList.remove('visible'),2500);}catch{$('#toast').textContent='Please copy the UPI ID shown above.';$('#toast').classList.add('visible');}}));
})();
