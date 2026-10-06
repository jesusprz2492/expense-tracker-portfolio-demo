const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let now=0, interval, calls=[]; const events={}, winEvents={};
const label={textContent:''}, shell={replaceWith(){}}, status={setAttribute(){}};
const document={documentElement:{lang:'en'},hidden:false,body:{append(){}},querySelector(s){return s==='.app-shell'?shell:s==='[data-demo-clock]'?label:status},querySelectorAll(){return []},addEventListener(k,f){events[k]=f}};
const sandbox={document,window:{addEventListener(k,f){winEvents[k]=f},scrollTo(){}},location:{href:'https://demo.test/movements',origin:'https://demo.test'},history:{pushState(){},replaceState(){}},Date:{now:()=>now},URL,URLSearchParams,FormData:class {constructor(f){return Object.entries(f.data)[Symbol.iterator]()}},DOMParser:class{parseFromString(){return document}},setInterval(f){interval=f},alert(m){throw Error(m)},confirm:()=>true,fetch:async(u,o)=>{calls.push(JSON.parse(o.body));return {ok:true,text:async()=>''}}};
for(const fn of ['initializeDialogs','initializeMovementEditor','initializePaymentMethodEditor','initializeAccountEditor','initializeContactEditor']) sandbox[fn]=()=>{};
vm.runInNewContext(fs.readFileSync('app/static/js/demo.js','utf8'),sandbox);
const tick=()=>new Promise(setImmediate);
(async()=>{
  events.DOMContentLoaded();
  events.submit({preventDefault(){},target:{method:'post',action:'https://demo.test/movements',data:{month_id:'2026-10',description:'temporary',amount:'25'}}}); await tick();
  assert.equal(calls.at(-1).operations.length,1);
  now=3599999; interval(); await tick(); assert.equal(calls.length,1);
  now=3600000; interval(); await tick(); assert.equal(calls.at(-1).operations.length,0); assert.match(label.textContent,/60 min/);
  events.submit({preventDefault(){},target:{method:'post',action:'https://demo.test/movements',data:{month_id:'2026-10',description:'temporary',amount:'25'}}}); await tick();
  winEvents.pagehide();winEvents.pageshow({persisted:true});await tick();assert.equal(calls.at(-1).operations.length,0);
  console.log('PASS: edited state resets at 60 minutes and after pagehide/BFCache restore');
})().catch(e=>{console.error(e);process.exitCode=1});
