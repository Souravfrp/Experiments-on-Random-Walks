"use strict";
/* The rounded-cube mixed-volume demo is a separate experiment.
 * No external service, network upload, or Python/C++ runtime is involved.
 */
(() => {
  const $=id=>document.getElementById(id);
  let worker=null,latest=null;
  const fmt=(v,d=4)=>Number.isFinite(v)?Number(v).toLocaleString("en-US",{maximumFractionDigits:d}):"—";
  function status(value,error=false){$("mv-status").textContent=value;$("mv-status").className=error?"simulation-status error":"simulation-status";}
  function setBusy(b){$("mv-start").disabled=b;$("mv-cancel").disabled=!b;$("mv-export").disabled=b||!latest;}
  function configureK(){
    const n=Number($("mv-dimension").value),select=$("mv-component");
    const old=Number(select.value);
    select.replaceChildren();
    for(let j=0;j<=n;j++){
      const opt=document.createElement("option");opt.value=String(j);
      opt.textContent="k = "+j+(j===0?" (cube interior)":j===n?" (vertex regions)":"");
      select.appendChild(opt);
    }
    select.value=String(old<=n?old:Math.min(n,2));
  }
  function params(){
    const p={n:Number($("mv-dimension").value),
      lambda:Number($("mv-lambda").value),
      k:Number($("mv-component").value),
      samples:Number($("mv-samples").value),
      seed:Number($("mv-seed").value)};
    if(!Number.isSafeInteger(p.n)||p.n<1||p.n>6)throw Error("Choose a dimension from 1 to 6.");
    if(!$("mv-lambda").value.trim()||!Number.isFinite(p.lambda)||p.lambda<0.1||p.lambda>2)throw Error("Choose λ between 0.1 and 2.");
    if(!Number.isSafeInteger(p.k)||p.k<0||p.k>p.n)throw Error("Choose a valid component index k.");
    if(!Number.isSafeInteger(p.samples)||p.samples<1000||p.samples>50000)throw Error("Choose 1,000 to 50,000 samples.");
    if(!$("mv-seed").value.trim()||!Number.isSafeInteger(p.seed)||p.seed<0||p.seed>4294967295)throw Error("Enter an integer seed from 0 to 4,294,967,295.");
    return p;
  }
  function table(p){
    const tbody=$("mv-terms");tbody.replaceChildren();
    for(const component of p.components){
      const j=component.k,tr=document.createElement("tr");
      const values=[String(j),
        fmt(component.mixedVolume,6),
        fmt(component.exactProbability*100,3)+"%",
        fmt(p.componentEstimates[j]===null?NaN:p.componentEstimates[j]*100,3)+"%",
        fmt(p.counts[j],0)];
      for(const value of values){const td=document.createElement("td");td.textContent=value;tr.appendChild(td);}
      tbody.appendChild(tr);
    }
  }
  function plot(p){
    const canvas=$("mv-chart"),ctx=canvas.getContext("2d");
    const dpi=window.devicePixelRatio||1,w=canvas.clientWidth||750,h=canvas.clientHeight||300;
    canvas.width=Math.round(w*dpi);canvas.height=Math.round(h*dpi);
    ctx.setTransform(dpi,0,0,dpi,0,0);ctx.clearRect(0,0,w,h);
    ctx.fillStyle="#fcfdfc";ctx.fillRect(0,0,w,h);
    const left=57,right=w-15,top=24,bottom=h-48,max=Math.max(.05,...p.components.map(z=>z.exactProbability*1.12));
    ctx.font="12px system-ui";ctx.fillStyle="#52635a";ctx.textAlign="left";
    const ymax=Math.min(1,Math.max(.1,max)),dy=bottom-top;
    for(let i=0;i<=4;i++){
      const v=i*ymax/4,y=bottom-v/ymax*dy;
      ctx.strokeStyle="#e5eee9";ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.stroke();
      ctx.fillStyle="#647369";ctx.fillText((v*100).toFixed(0)+"%",7,y+4);
    }
    const n=p.parameters.n,m=p.components.length,slot=(right-left)/m,bw=Math.min(28,slot*.31);
    for(let j=0;j<m;j++){
      const center=left+(j+.5)*slot,c=p.components[j],estimated=p.componentEstimates[j];
      const exactY=c.exactProbability/ymax*dy;
      ctx.fillStyle="#2f7167";ctx.fillRect(center-bw-2,bottom-exactY,bw,exactY);
      if(estimated!==null){
        const measuredY=estimated/ymax*dy;ctx.fillStyle="#9db2dd";ctx.fillRect(center+2,bottom-measuredY,bw,measuredY);
      }
      ctx.fillStyle="#465a51";ctx.textAlign="center";ctx.fillText(String(j),center,bottom+19);
    }
    ctx.textAlign="left";ctx.fillStyle="#5a6e64";ctx.fillText("Component index k · exact versus sampled probabilities",left,bottom+39);
  }
  function present(p){
    latest=p;setBusy(false);$("mv-output").hidden=false;
    $("mv-volume-exact").textContent=fmt(p.exactVolume,6);
    $("mv-volume-est").textContent=fmt(p.volumeEstimate,6);
    $("mv-volume-range").textContent=fmt(p.volumeInterval[0],6)+" – "+fmt(p.volumeInterval[1],6);
    $("mv-mixed-exact").textContent=fmt(p.exactMixedVolume,6);
    $("mv-mixed-est").textContent=fmt(p.estimatedMixedVolume,6);
    $("mv-mixed-range").textContent=fmt(p.coefficientInterval[0],6)+" – "+fmt(p.coefficientInterval[1],6);
    $("mv-acceptance").textContent=fmt(100*p.inside/p.parameters.samples,2)+"%";
    $("mv-target-hits").textContent=fmt(p.targetHits,0)+" of "+fmt(p.parameters.samples,0)+" samples";
    $("mv-elapsed").textContent=fmt(p.elapsedMs,1)+" ms";
    const intro="New independent bounding-box Monte Carlo experiment · n="+p.parameters.n+
      ", λ="+p.parameters.lambda+", k="+p.parameters.k+", N="+p.parameters.samples+", seed="+p.parameters.seed+".";
    $("mv-experiment-summary").textContent=intro;
    $("mv-rare-warning").hidden=p.targetHits>=10;
    table(p);plot(p);
    status("Calculation completed locally. Nothing was uploaded.");
    $("mv-output").scrollIntoView({block:"start",behavior:"smooth"});
  }
  function download(p){
    const header=["dimension","lambda","samples","seed","k","count_inside","count_k","exact_coefficient","estimated_coefficient","exact_component_probability","estimated_component_probability","exact_volume","estimated_volume"];
    const lines=[header.join(",")];
    for(const c of p.components){
      const j=c.k;
      lines.push([p.parameters.n,p.parameters.lambda,p.parameters.samples,p.parameters.seed,j,p.inside,p.counts[j],
        c.mixedVolume,p.envelopeVolume*(p.counts[j]/p.parameters.samples)/(Math.round(binomial(p.parameters.n,j))*Math.pow(p.parameters.lambda,j)),
        c.exactProbability,p.componentEstimates[j]===null?"":p.componentEstimates[j],p.exactVolume,p.volumeEstimate].join(","));
    }
    const url=URL.createObjectURL(new Blob([lines.join("\r\n")+"\r\n"],{type:"text/csv;charset=utf-8"}));
    const a=document.createElement("a");a.href=url;a.download="rounded_cube_mixed_volume_n"+p.parameters.n+"_seed"+p.parameters.seed+".csv";
    document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),0);
  }
  function binomial(n,j){let x=1;for(let i=1;i<=j;i++)x=x*(n+1-i)/i;return x;}
  document.addEventListener("DOMContentLoaded",()=>{
    $("mv-dimension").addEventListener("change",configureK);configureK();
    $("mv-demo-3").addEventListener("click",()=>{
      $("mv-dimension").value="3";configureK();$("mv-component").value="2";
      $("mv-lambda").value="1";$("mv-samples").value="12000";$("mv-seed").value="2026";
    });
    $("mv-demo-5").addEventListener("click",()=>{
      $("mv-dimension").value="5";configureK();$("mv-component").value="3";
      $("mv-lambda").value="1.5";$("mv-samples").value="20000";$("mv-seed").value="2026";
    });
    $("mv-cancel").addEventListener("click",()=>{
      if(worker)worker.terminate();worker=null;setBusy(false);status("Calculation cancelled.");
    });
    $("mv-form").addEventListener("submit",ev=>{
      ev.preventDefault();
      let p;try{p=params();}catch(e){status(e.message,true);return;}
      if(worker)worker.terminate();
      latest=null;$("mv-output").hidden=true;setBusy(true);status("Sampling independent points in the bounding cube…");
      worker=new Worker("./mixed_volume_worker.js");
      worker.onmessage=ev=>{
        const m=ev.data;
        if(m.type==="progress")status("Evaluated "+fmt(m.samplesDone,0)+" of "+fmt(m.samples,0)+" points…");
        if(m.type==="error"){status(m.message,true);worker.terminate();worker=null;setBusy(false);}
        if(m.type==="done"){present(m.payload);worker.terminate();worker=null;setBusy(false);}
      };
      worker.onerror=ev=>{status(ev.message||"Worker failed",true);worker.terminate();worker=null;setBusy(false);};
      worker.postMessage(p);
    });
    $("mv-export").addEventListener("click",()=>{if(latest)download(latest);});
    window.addEventListener("resize",()=>{if(latest&&!$("mv-output").hidden)plot(latest);});
    setBusy(false);
  });
})();
