"use strict";
/* Real browser-side simulations. These are not native Python/C++ timings. */
(() => {
  const COLORS={ball:"#377db3",dikin:"#db8937",coordinate_hit_run:"#25866a",random_hit_run:"#be5269",john:"#8065b5"};
  const LABELS={ball:"Ball Walk",dikin:"Dikin Walk",coordinate_hit_run:"Coordinate Hit-and-Run",random_hit_run:"Random Hit-and-Run",john:"John's Walk"};
  const $=id=>document.getElementById(id);
  let worker=null, latest=null;
  const num=(value,d=3)=> value===null||value===undefined||!Number.isFinite(value)?"—":Number(value).toLocaleString("en-US",{maximumFractionDigits:d});

  function status(text,kind="") {
    $("run-status").textContent=text;
    $("run-status").className="simulation-status "+kind;
  }
  function readForm(){
    const o={
      n:Number($("run-dimension").value),
      walk:$("run-walk").value,
      steps:Number($("run-steps").value),
      chains:Number($("run-chains").value),
      seed:Number($("run-seed").value)
    };
    for(const key of ["n","steps","chains","seed"]){
      if(!$("run-"+({n:"dimension",steps:"steps",chains:"chains",seed:"seed"}[key])).value.trim())
        throw Error("Enter a valid "+key+" value.");
    }
    if(!Number.isSafeInteger(o.n)||o.n<1||o.n>30)throw Error("Dimension n must be an integer from 1 to 30.");
    if(!Number.isSafeInteger(o.steps)||o.steps<16||o.steps>2048)throw Error("Steps must be an integer from 16 to 2048.");
    if(!Number.isSafeInteger(o.chains)||o.chains<30||o.chains>1000)throw Error("Chains must be an integer from 30 to 1000.");
    if(!Number.isSafeInteger(o.seed)||o.seed<0||o.seed>4294967295)throw Error("Seed must be an integer from 0 to 4,294,967,295.");
    const quantity=o.walk==="all"?5:1;
    if(o.n*o.steps*o.chains*quantity>8000000)
      throw Error("This selection is too expensive for a browser experiment. Reduce dimension, steps, or chains, or select one walk (limit: 8 million coordinate-updates).");
    return o;
  }
  function describeWork(){
    try{
      const p=readForm(), count=p.walk==="all"?5:1;
      $("run-budget").textContent="Selected workload: "+num(count*p.steps*p.chains*p.n,0)+" coordinate-updates (maximum 8,000,000).";
      $("run-budget").className="run-help";
    }catch(e){
      $("run-budget").textContent=e.message;
      $("run-budget").className="run-help run-invalid";
    }
  }
  function busy(value){
    $("run-start").disabled=value;
    $("run-cancel").disabled=!value;
    $("run-export").disabled=value||!latest;
  }
  function td(tr,text){
    const el=document.createElement("td");el.textContent=text;tr.appendChild(el);return el;
  }
  function writeTable(results){
    const body=$("live-rows");body.replaceChildren();
    for(const item of results){
      const final=item.checkpoints[item.checkpoints.length-1];
      const tr=document.createElement("tr");
      td(tr,LABELS[item.walk]);
      td(tr,num(final.ks,4));
      td(tr,num(final.momentError,4));
      td(tr,item.proxy_steps===null?"Not reached":num(item.proxy_steps,0));
      td(tr,num(item.acceptance*100,1)+"%");
      td(tr,num(item.elapsed_ms,1));
      const exact=td(tr,item.exact_coordinate_tv===null?"—":num(item.exact_coordinate_tv,5));
      exact.title=item.exact_coordinate_tv===null?"No exact reference established for this walk":"Exact full-law total variation at the specified number of steps";
      body.appendChild(tr);
    }
  }
  function setCanvas(canvas){
    const ctx=canvas.getContext("2d"), dpr=window.devicePixelRatio||1;
    const width=canvas.clientWidth||700,height=canvas.clientHeight||310;
    canvas.width=Math.floor(width*dpr);canvas.height=Math.floor(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,width,height);
    ctx.fillStyle="#fcfdfc";ctx.fillRect(0,0,width,height);
    return {ctx,width,height};
  }
  function drawEmpty(canvas,message){
    const {ctx}=setCanvas(canvas);
    ctx.font="14px system-ui,sans-serif";ctx.fillStyle="#6a7770";ctx.fillText(message,20,40);
  }
  function chart(results){
    const {ctx,width,height}=setCanvas($("run-curve"));
    const left=57,right=width-22,top=26,bottom=height-55;
    ctx.strokeStyle="#e2e9e5";ctx.lineWidth=1;
    ctx.font="12px system-ui,sans-serif";ctx.fillStyle="#566b61";
    for(let tick=0;tick<=5;tick++){
      const v=tick*.1,y=bottom-(v/.5)*(bottom-top);
      ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.stroke();
      ctx.fillText(v.toFixed(1),12,y+4);
    }
    const maxSteps=results.reduce((m,r)=>Math.max(m,r.checkpoints[r.checkpoints.length-1].step),16);
    const tx=t=>left+Math.log2(t)/Math.log2(maxSteps)*(right-left);
    for(let p=1;p<=maxSteps;p*=2){
      const x=tx(p);
      ctx.strokeStyle="#edf0ed";ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,bottom);ctx.stroke();
      ctx.fillStyle="#53615b";ctx.fillText(String(p),x-6,bottom+19);
    }
    for(const item of results) {
      ctx.strokeStyle=COLORS[item.walk];ctx.fillStyle=COLORS[item.walk];ctx.lineWidth=2.3;
      ctx.beginPath();
      item.checkpoints.forEach((z,i)=>{
        const x=tx(z.step),y=bottom-Math.min(0.5,z.ks)/0.5*(bottom-top);
        if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
      });
      ctx.stroke();
      for(const z of item.checkpoints){
        const x=tx(z.step),y=bottom-Math.min(0.5,z.ks)/0.5*(bottom-top);
        ctx.beginPath();ctx.arc(x,y,2.7,0,Math.PI*2);ctx.fill();
      }
    }
    const yy=bottom-.15/.5*(bottom-top);
    ctx.strokeStyle="#4a7266";ctx.setLineDash([6,5]);ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(right,yy);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle="#4a7266";ctx.fillText("KS threshold 0.15",Math.max(left+5,right-142),yy-8);
    ctx.fillStyle="#4d635c";ctx.fillText("Checkpoint (log₂ steps)",left,bottom+44);
    ctx.save();ctx.translate(13,top+110);ctx.rotate(-Math.PI/2);ctx.fillText("KS discrepancy",0,0);ctx.restore();
  }
  function scatter(item,n){
    const {ctx,width,height}=setCanvas($("run-spread"));
    const left=48,right=width-22,top=24,bottom=height-50,col=COLORS[item.walk];
    if(n===1) {
      const counts=Array(20).fill(0);
      for(const [x] of item.endpoints)counts[Math.min(19,Math.max(0,Math.floor((x+.5)*20)))]++;
      const mx=Math.max(1,...counts);
      for(let i=0;i<20;i++){
        const a=left+i*(right-left)/20,h=counts[i]/mx*(bottom-top);
        ctx.fillStyle=col;ctx.globalAlpha=.76;ctx.fillRect(a+1,bottom-h,(right-left)/20-2,h);
      }
      ctx.globalAlpha=1;ctx.fillStyle="#52635d";ctx.font="12px system-ui";
      ctx.fillText("First coordinate (20-bin histogram)",left,bottom+30);
    }else{
      ctx.strokeStyle="#b5c8bf";ctx.strokeRect(left,top,right-left,bottom-top);
      ctx.strokeStyle="#edf0ec";ctx.beginPath();
      ctx.moveTo((left+right)/2,top);ctx.lineTo((left+right)/2,bottom);
      ctx.moveTo(left,(top+bottom)/2);ctx.lineTo(right,(top+bottom)/2);ctx.stroke();
      ctx.fillStyle=col;ctx.globalAlpha=.42;
      for(const [x,y] of item.endpoints){
        const px=left+(x+.5)*(right-left),py=bottom-(y+.5)*(bottom-top);
        ctx.beginPath();ctx.arc(px,py,2.5,0,2*Math.PI);ctx.fill();
      }
      ctx.globalAlpha=1;ctx.font="12px system-ui";ctx.fillStyle="#52635d";
      ctx.fillText("First two coordinates (projection)",left,bottom+30);
      ctx.fillText("−0.5",left-3,bottom+14);ctx.fillText("0.5",right-17,bottom+14);
    }
  }
  function show(results,params){
    if(!results.length)return;
    $("live-output").hidden=false;
    writeTable(results);chart(results);
    $("run-display-walk").replaceChildren();
    for(const r of results){
      const option=document.createElement("option");
      option.value=r.walk;option.textContent=LABELS[r.walk];$("run-display-walk").appendChild(option);
    }
    function selected(){
      const r=results.find(x=>x.walk===$("run-display-walk").value)||results[0];
      scatter(r,params.n);
    }
    $("run-display-walk").onchange=selected;selected();
    $("run-summary").textContent="Fresh in-browser experiment · n="+params.n+", "+params.steps+" transitions per chain, "+params.chains+" independent chains, seed "+params.seed+". These are JavaScript computations performed on this device, not measurements of Python or C++.";
    $("live-output").scrollIntoView({behavior:"smooth",block:"start"});
  }
  function csv(results,p){
    const head=["engine","n","steps","chains","seed","walk","checkpoint_step","ks","pair_ks","moment_relative_error","acceptance","elapsed_ms_total","empirical_proxy_steps","exact_coordinate_tv_at_final"];
    const lines=[head.join(",")];
    for(const r of results)for(const c of r.checkpoints){
      lines.push(["browser_javascript",p.n,p.steps,p.chains,p.seed,r.walk,
        c.step,c.ks,c.pairKs,c.momentError,c.acceptance,r.elapsed_ms,
        r.proxy_steps===null?"":r.proxy_steps,r.exact_coordinate_tv===null?"":r.exact_coordinate_tv].join(","));
    }
    return lines.join("\r\n")+"\r\n";
  }
  function download(text,name){
    const url=URL.createObjectURL(new Blob([text],{type:"text/csv;charset=utf-8"}));
    const link=document.createElement("a");link.href=url;link.download=name;document.body.appendChild(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),0);
  }
  document.addEventListener("DOMContentLoaded",()=>{
    $("run-form").addEventListener("input",describeWork);
    $("run-form").addEventListener("change",describeWork);
    $("run-example-small").addEventListener("click",()=>{
      $("run-dimension").value="2";$("run-steps").value="128";$("run-chains").value="200";$("run-seed").value="2026";$("run-walk").value="all";describeWork();
    });
    $("run-example-higher").addEventListener("click",()=>{
      $("run-dimension").value="20";$("run-steps").value="512";$("run-chains").value="200";$("run-seed").value="2026";$("run-walk").value="all";describeWork();
    });
    $("run-cancel").addEventListener("click",()=>{
      if(worker)worker.terminate();worker=null;busy(false);
      status("Experiment cancelled. No information was uploaded.");
    });
    $("run-form").addEventListener("submit",event=>{
      event.preventDefault();let params;
      try{params=readForm();}catch(e){status(e.message,"error");return;}
      if(worker)worker.terminate();
      latest=null;busy(true);$("live-output").hidden=true;
      status("Starting computation in this browser…");
      worker=new Worker("./sim_worker.js");
      worker.onmessage=event=>{
        const m=event.data;
        if(m.type==="start")status("Computing independent chains from the origin…");
        if(m.type==="progress")status("Computing "+LABELS[m.walk]+" ("+m.index+"/"+m.total+"), step "+m.step+"/"+m.steps+"…");
        if(m.type==="partial")status("Completed "+m.index+" of "+m.total+" walk(s)…");
        if(m.type==="error"){
          status(m.message,"error");worker.terminate();worker=null;busy(false);
        }
        if(m.type==="done"){
          latest=m.payload;show(latest.results,latest.parameters);
          status("Experiment completed on your device. Nothing was uploaded.","success");
          worker.terminate();worker=null;busy(false);
        }
      };
      worker.onerror=e=>{
        status("Unable to run the browser experiment: "+(e.message||"worker error"),"error");
        worker.terminate();worker=null;busy(false);
      };
      worker.postMessage(params);
    });
    $("run-export").addEventListener("click",()=>{
      if(latest)download(csv(latest.results,latest.parameters),"browser_random_walks_n"+latest.parameters.n+"_seed"+latest.parameters.seed+".csv");
    });
    window.addEventListener("resize",()=>{
      if(latest&&!$("live-output").hidden){
        chart(latest.results);
        const item=latest.results.find(r=>r.walk===$("run-display-walk").value)||latest.results[0];
        scatter(item,latest.parameters.n);
      }
    });
    describeWork();
    drawEmpty($("run-curve"),"Run an experiment to display convergence diagnostics.");
    drawEmpty($("run-spread"),"The endpoint distribution will appear here.");
    busy(false);
  });
})();
