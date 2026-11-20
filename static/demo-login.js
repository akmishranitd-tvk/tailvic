// Public demo identities only. This is intentionally not real authentication.
(()=>{'use strict';
const root=document.querySelector('[data-demo-page]');if(!root)return;
const key='tailvic-demo-role',accounts={customer:'customer@tailvic.example',admin:'admin@tailvic.example'};
let role=null;try{role=sessionStorage.getItem(key);}catch{}
const destination=r=>r==='admin'?'/admin/':'/account/dashboard/';
if(root.dataset.demoPage==='login'){
 if(role==='admin'||role==='customer'){location.replace(destination(role));return;}
 const form=root.querySelector('[data-demo-login]'),email=document.getElementById('demo-email'),password=document.getElementById('demo-password'),error=root.querySelector('[data-demo-error]');
 root.querySelectorAll('[data-demo-fill]').forEach(button=>button.addEventListener('click',()=>{email.value=accounts[button.dataset.demoFill];password.value='TailvicDemo2026!';error.hidden=true;email.focus();}));
 form.addEventListener('submit',event=>{event.preventDefault();const selected=Object.keys(accounts).find(r=>accounts[r]===email.value.trim().toLowerCase());if(!selected||password.value!=='TailvicDemo2026!'){error.hidden=false;return;}try{sessionStorage.setItem(key,selected);location.assign(destination(selected));}catch{error.textContent='Allow session storage in this browser to sign in.';error.hidden=false;}});
 root.querySelector('[data-demo-submit]').disabled=false;
}else{
 const expected=root.dataset.demoPage;
 if(role!==expected){location.replace(role==='admin'||role==='customer'?destination(role):'/account/');return;}
 root.querySelector('.demo-checking').hidden=true;root.querySelector('[data-demo-protected]').hidden=false;
 root.querySelector('[data-demo-logout]').addEventListener('click',()=>{try{sessionStorage.removeItem(key);}catch{}location.replace('/account/');});
}
})();
