"use strict";
/*
 * Small, independent IID rejection-sampling experiment for the rounded cube.
 * Geometry: P=[-1,1]^n and Q=P+lambda B_2^n (NOT the random-walk cube).
 *
 * Classification label j: number of coordinates with |x_i|>1.
 * Exact component region volume: binom(n,j) * 2^(n-j) * kappa_j * lambda^j.
 * Samples are independent uniform draws in [-1-lambda,1+lambda]^n.
 * This is NOT the hit-and-run B1/B2/B3 oracle algorithm in the thesis.
 */
const makeRng = seed => {
  let state=seed>>>0;
  return () => {
    state=(state+0x6d2b79f5)>>>0;
    let t=state;
    t=Math.imul(t^(t>>>15),t|1);
    t^=t+Math.imul(t^(t>>>7),t|61);
    return ((t^(t>>>14))>>>0)/4294967296;
  };
};
function kappa(j) {
  if(j===0)return 1;
  if(j===1)return 2;
  return 2*Math.PI*kappa(j-2)/j;
}
function binomial(n,j) {
  let result=1;
  for(let k=1;k<=j;k++)result=result*(n+1-k)/k;
  return result;
}
function validate(p){
  const n=Number(p.n),lambda=Number(p.lambda),samples=Number(p.samples),
        k=Number(p.k),seed=Number(p.seed);
  if(!Number.isSafeInteger(n)||n<1||n>6)throw Error("Dimension must be an integer from 1 to 6.");
  if(!Number.isFinite(lambda)||lambda<0.1||lambda>2)throw Error("Lambda must be between 0.1 and 2.");
  if(!Number.isSafeInteger(samples)||samples<1000||samples>50000)throw Error("Samples must be an integer between 1,000 and 50,000.");
  if(!Number.isSafeInteger(k)||k<0||k>n)throw Error("Target component k must be an integer from 0 through n.");
  if(!Number.isSafeInteger(seed)||seed<0||seed>4294967295)throw Error("Seed must be an integer from 0 to 4,294,967,295.");
  return {n,lambda,samples,k,seed};
}
function wilson(count,total,z=1.959963984540054) {
  const p=count/total,zz=z*z,denom=1+zz/total;
  const mid=(p+zz/(2*total))/denom;
  const half=z/denom*Math.sqrt(p*(1-p)/total+zz/(4*total*total));
  return [Math.max(0,mid-half),Math.min(1,mid+half)];
}
function compute(p) {
  const {n,lambda,samples,k,seed}=p;
  const rng=makeRng(seed), cubeSide=2*(1+lambda);
  const envelopeVolume=Math.pow(cubeSide,n),counts=Array(n+1).fill(0);
  const terms=Array.from({length:n+1},(_,j)=>
    binomial(n,j)*Math.pow(2,n-j)*kappa(j)*Math.pow(lambda,j));
  const exactVolume=terms.reduce((a,b)=>a+b,0);
  const components=Array.from({length:n+1},(_,j)=>({k:j,
    mixedVolume:Math.pow(2,n-j)*kappa(j),
    exactTerm:terms[j],exactProbability:terms[j]/exactVolume}));
  let inside=0;
  const started=performance.now();
  for(let s=0;s<samples;s++){
    let d2=0,j=0;
    for(let i=0;i<n;i++){
      const x=(2*rng()-1)*(1+lambda);
      const outside=Math.max(0,Math.abs(x)-1);
      if(outside>0)j++;
      d2+=outside*outside;
    }
    if(d2 <= lambda*lambda) {inside++;counts[j]++;}
    if((s+1)%10000===0)self.postMessage({type:"progress",samplesDone:s+1,samples});
  }
  const ms=performance.now()-started;
  const volumeEstimate=envelopeVolume*inside/samples;
  const volumeInterval=wilson(inside,samples).map(x=>x*envelopeVolume);
  const coefficientScale=envelopeVolume/(binomial(n,k)*Math.pow(lambda,k));
  const coefficientEstimate=coefficientScale*counts[k]/samples;
  const coefficientInterval=wilson(counts[k],samples).map(x=>x*coefficientScale);
  return {parameters:p,engine:"IID bounding-box Monte Carlo in browser JavaScript",inside,
    envelopeVolume,exactVolume,volumeEstimate,volumeInterval,components,
    counts,componentEstimates:counts.map(c=>inside?c/inside:null),
    exactMixedVolume:components[k].mixedVolume,estimatedMixedVolume:coefficientEstimate,
    coefficientInterval,targetHits:counts[k],elapsedMs:ms};
}
self.onmessage=function(event){
  try{
    const p=validate(event.data);
    self.postMessage({type:"done",payload:compute(p)});
  }catch(error) {
    self.postMessage({type:"error",message:error.message||String(error)});
  }
};
