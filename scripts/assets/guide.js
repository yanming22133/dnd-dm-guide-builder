/* ---------------- 搜索 / 导航 / 骰子 / 记录 ---------------- */
const q = document.getElementById('q');
q.addEventListener('input', ()=>{
  const v = q.value.trim().toLowerCase();
  document.querySelectorAll('.card.area, .card.monster, .card.item, .card.npc').forEach(c=>{
    c.classList.toggle('hidden', v && !(c.dataset.search||c.textContent).toLowerCase().includes(v));
  });
});
document.querySelectorAll('.nav-group').forEach(g=>{ if(g.querySelector('.nav-sub')) g.classList.add('open'); });
const obs = new IntersectionObserver(es=>{
  es.forEach(e=>{ if(e.isIntersecting){
    document.querySelectorAll('aside.side a.active').forEach(a=>{a.classList.remove('active');a.style.background='';});
    const a = document.querySelector('aside.side a[href="#'+e.target.id+'"]');
    if(a){a.classList.add('active'); a.style.background='#3a2c18';}
  }});
},{rootMargin:'-70px 0px -75% 0px'});
document.querySelectorAll('.card.area, section').forEach(s=>obs.observe(s));
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{
  const t=document.querySelector(c.getAttribute('href'));
  if(t){t.style.transition='none';t.style.outline='2px solid #d9b34a';setTimeout(()=>{t.style.outline='';},1400);}
}));
document.querySelectorAll('.dice button').forEach(b=>b.addEventListener('click',()=>{
  const n=parseInt(b.dataset.die,10);
  document.getElementById('diceOut').textContent='d'+n+' → '+(1+Math.floor(Math.random()*n));
}));
const tt=document.getElementById('toTop');
window.addEventListener('scroll',()=>{tt.style.display=window.scrollY>500?'block':'none';});
tt.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
document.getElementById('printBtn').addEventListener('click',()=>window.print());

/* ---------------- 地图悬浮窗 ---------------- */
const MAPS = __MAPS_JSON__;
const win = document.getElementById('mapWin');
const body = document.getElementById('mwBody');
const img = document.getElementById('mwImg');
const titleEl = document.getElementById('mwTitle');
const SK = 'lmop_map_win_v1';
let st = {map:'castle', min:false, left:null, top:null, w:null, h:null, scale:1, tx:0, ty:0};
try{ Object.assign(st, JSON.parse(localStorage.getItem(SK)||'{}')); }catch(e){}
function saveSt(){ try{ localStorage.setItem(SK, JSON.stringify(st)); }catch(e){} }

function clampPos(){
  const w = win.offsetWidth, h = win.offsetHeight;
  const maxL = Math.max(0, innerWidth - w), maxT = Math.max(0, innerHeight - h);
  if(st.left==null||isNaN(st.left)) st.left = Math.max(8, innerWidth - w - 16);
  if(st.top==null||isNaN(st.top))   st.top  = Math.max(8, innerHeight - h - 16);
  st.left = Math.min(Math.max(0, st.left), maxL);
  st.top  = Math.min(Math.max(0, st.top),  maxT);
}
function defaultSize(){
  const w = st.w || Math.min(Math.round(innerWidth*0.5), 860);
  const h = st.h || Math.min(Math.round(innerHeight*0.72), 820);
  return [Math.max(300,w), Math.max(200,h)];
}
function layout(){
  const [w,h] = defaultSize();
  win.style.width = w+'px';
  win.style.height = (st.min? 0 : h)+'px';
  win.style.height = st.min? 'auto' : h+'px';
  clampPos();
  win.style.left = st.left+'px'; win.style.top = st.top+'px';
  win.classList.toggle('min', !!st.min);
}
function apply(){ img.style.transform = 'translate('+st.tx+'px,'+st.ty+'px) scale('+st.scale+')'; }
function fit(){
  const M = MAPS[st.map];
  const W = body.clientWidth||600, H = body.clientHeight||400;
  const s = Math.min(W/M.w, H/M.h) * 0.97;
  st.scale = s; st.tx = (W - M.w*s)/2; st.ty = (H - M.h*s)/2;
  img.style.width = M.w+'px'; img.style.height = M.h+'px';
  apply();
}
function setMap(key){
  if(key && MAPS[key]) st.map = key;
  const M = MAPS[st.map];
  img.src = M.uri; titleEl.textContent = M.title;
  document.querySelectorAll('.mw-tabs button').forEach(t=>t.classList.toggle('active', t.dataset.map===st.map));
  saveSt();
}
function show(key){ st.min=false; win.classList.remove('hide'); if(key) setMap(key); layout(); setMap(st.map); requestAnimationFrame(fit); saveSt(); }
function toggle(){ if(win.classList.contains('hide')||st.min) show(); else { win.classList.add('hide'); saveSt(); } }

document.querySelectorAll('[data-map-open]').forEach(el=>el.addEventListener('click',()=>show(el.dataset.mapOpen)));
document.getElementById('fab').addEventListener('click',()=>show());
document.getElementById('mwMin').addEventListener('click',()=>{ st.min=!st.min; layout(); saveSt(); if(!st.min) requestAnimationFrame(fit); });
document.getElementById('mwClose').addEventListener('click',()=>{ win.classList.add('hide'); saveSt(); });
document.getElementById('mwHalf').addEventListener('click',()=>{ st.min=false; st.w=Math.round(innerWidth*0.5); st.h=Math.round(innerHeight*0.82); st.left=innerWidth-st.w-16; st.top=Math.max(8,innerHeight-st.h-16); layout(); requestAnimationFrame(fit); saveSt(); });
document.getElementById('mwFull').addEventListener('click',()=>{ st.min=false; st.w=innerWidth-24; st.h=innerHeight-24; st.left=12; st.top=12; layout(); requestAnimationFrame(fit); saveSt(); });
document.getElementById('mwIn').addEventListener('click',()=>{ st.scale*=1.25; apply(); saveSt(); });
document.getElementById('mwOut').addEventListener('click',()=>{ st.scale/=1.25; apply(); saveSt(); });
document.getElementById('mwFit').addEventListener('click',()=>{ fit(); saveSt(); });
document.querySelectorAll('.mw-tabs button').forEach(t=>t.addEventListener('click',()=>{ setMap(t.dataset.map); requestAnimationFrame(fit); }));
body.addEventListener('wheel',e=>{ e.preventDefault(); st.scale *= (e.deltaY<0?1.15:0.87); apply(); saveSt(); },{passive:false});
document.addEventListener('keydown',e=>{ if(e.key==='Escape') win.classList.add('hide'); });

/* 拖动地图内容 */
let pan=null;
body.addEventListener('pointerdown',e=>{ if(e.target.id==='mwResize') return; pan={x:e.clientX-st.tx,y:e.clientY-st.ty}; body.classList.add('drag'); body.setPointerCapture(e.pointerId); });
body.addEventListener('pointermove',e=>{ if(pan){ st.tx=e.clientX-pan.x; st.ty=e.clientY-pan.y; apply(); } });
body.addEventListener('pointerup',e=>{ pan=null; body.classList.remove('drag'); saveSt(); });
body.addEventListener('pointercancel',()=>{ pan=null; body.classList.remove('drag'); });

/* 拖动窗口 */
const bar = document.getElementById('mwBar');
let dg=null;
bar.addEventListener('pointerdown',e=>{ if(e.target.closest('button')) return; dg={x:e.clientX-st.left,y:e.clientY-st.top}; bar.setPointerCapture(e.pointerId); });
bar.addEventListener('pointermove',e=>{ if(dg){ st.left=e.clientX-dg.x; st.top=e.clientY-dg.y; clampPos(); win.style.left=st.left+'px'; win.style.top=st.top+'px'; } });
bar.addEventListener('pointerup',()=>{ dg=null; saveSt(); });

/* 缩放窗口 */
const rz = document.getElementById('mwResize');
let rs=null;
rz.addEventListener('pointerdown',e=>{ e.stopPropagation(); rs={x:e.clientX,y:e.clientY,w:win.offsetWidth,h:win.offsetHeight}; rz.setPointerCapture(e.pointerId); });
rz.addEventListener('pointermove',e=>{ if(rs){ st.w=Math.max(300, rs.w+(e.clientX-rs.x)); st.h=Math.max(200, rs.h+(e.clientY-rs.y)); st.min=false; layout(); requestAnimationFrame(fit); } });
rz.addEventListener('pointerup',()=>{ rs=null; saveSt(); });

window.addEventListener('resize',()=>{ clampPos(); win.style.left=st.left+'px'; win.style.top=st.top+'px'; if(!st.min) requestAnimationFrame(fit); });

setMap(st.map);
layout();
if(!localStorage.getItem(SK)){ st.min=true; layout(); }  /* 首次默认最小化，避免挡内容 */
img.addEventListener('load',()=>{ if(!st.min) fit(); });

/* ---------------- 先攻 / HP 追踪 ---------------- */
const TK='lmop_dm_tracker_v1';
let tk=[];
try{tk=JSON.parse(localStorage.getItem(TK)||'[]');}catch(e){tk=[];}
function saveTk(){try{localStorage.setItem(TK,JSON.stringify(tk));}catch(e){}}
function esc2(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function drawTk(){
  const box=document.getElementById('tkList');
  if(!tk.length){box.innerHTML='<p class="tip">还没有加入任何生物。输入名字、先攻、HP 后点「加入」。</p>';}
  else{
    box.innerHTML=tk.map((r,i)=>{
      const cls=r.hp<=0?'zero':(r.hp<=5?'low':'');
      return '<div class="tk-row"><span class="tk-name">'+esc2(r.name)+'</span>'
        +'<span class="tk-init">先攻 '+r.init+'</span><span class="tk-hp '+cls+'">HP '+r.hp+'</span>'
        +'<button data-a="-5" data-i="'+i+'">-5</button><button data-a="-1" data-i="'+i+'">-1</button>'
        +'<button data-a="1" data-i="'+i+'">+1</button><button data-a="5" data-i="'+i+'">+5</button>'
        +'<button data-a="del" data-i="'+i+'">✕</button></div>';
    }).join('');
  }
  box.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
    const i=+b.dataset.i, a=b.dataset.a;
    if(a==='del') tk.splice(i,1); else tk[i].hp=Math.max(-99,tk[i].hp+parseInt(a,10));
    saveTk(); drawTk();
  }));
}
document.getElementById('tkAdd').addEventListener('click',()=>{
  const n=document.getElementById('tkName').value.trim()||'怪物';
  const it=parseInt(document.getElementById('tkInit').value,10);
  const h=parseInt(document.getElementById('tkHp').value,10);
  tk.push({name:n, init:isNaN(it)?0:it, hp:isNaN(h)?10:h});
  tk.sort((a,b)=>b.init-a.init);
  document.getElementById('tkName').value='';document.getElementById('tkInit').value='';document.getElementById('tkHp').value='';
  saveTk(); drawTk();
});
drawTk();
