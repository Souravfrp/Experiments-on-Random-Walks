"use strict";
// No third-party dependencies. Validates formulas and seeded Monte Carlo estimates.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const source=fs.readFileSync(path.join(__dirname,"../site/mixed_volume_worker.js"),"utf8");
function run(params){
  const messages=[];
  const sandbox=vm.createContext({self:{postMessage:msg=>messages.push(msg)},performance:{now:()=>0}});
  vm.runInContext(source,sandbox,{filename:"mixed_volume_worker.js",timeout:10000});
  sandbox.self.onmessage({data:params});
  return {result:messages.find(m=>m.type==="done")?.payload,error:messages.find(m=>m.type==="error")?.message};
}
function approx(a,b,tolerance,message){assert.ok(Math.abs(a-b)<=tolerance,message+": "+a+" vs "+b);}
const p={n:3,lambda:1,samples:50000,seed:2026,k:2};
const a=run(p);
assert.ok(a.result, a.error);
const r=a.result;
const exact=8+24+6*Math.PI+4*Math.PI/3;
approx(r.exactVolume,exact,1e-10,"Exact cube + ball volume for n=3");
approx(r.exactMixedVolume,2*Math.PI,1e-12,"M_2 exact");
approx(r.components.reduce((s,c)=>s+c.exactProbability,0),1,1e-12,"Probabilities sum to one");
approx(r.volumeEstimate,exact,0.8,"Large-sample volume estimator");
approx(r.estimatedMixedVolume,2*Math.PI,.3,"Large-sample coefficient estimator");
assert.equal(r.counts.reduce((s,c)=>s+c,0),r.inside);
assert.ok(r.volumeInterval[0] <= r.volumeEstimate && r.volumeInterval[1] >= r.volumeEstimate);
assert.ok(r.coefficientInterval[0] <= r.estimatedMixedVolume && r.coefficientInterval[1] >= r.estimatedMixedVolume);
const b=run(p);assert.deepEqual(Array.from(b.result.counts),Array.from(r.counts),"Same inputs and seed produce the same counts");
const n1=run({n:1,lambda:1,samples:1000,seed:1,k:1}).result;
approx(n1.exactVolume,4,1e-12,"One-dimensional rounded interval volume");
approx(n1.components[0].mixedVolume,2,1e-12,"One-dimensional M0");
approx(n1.components[1].mixedVolume,2,1e-12,"One-dimensional M1");
const bad=run({...p,n:100});assert.match(bad.error,/Dimension/);
assert.equal(bad.result,undefined);
const badLambda=run({...p,lambda:-1});assert.match(badLambda.error,/Lambda/);
console.log("Mixed-volume tests passed: exact coefficients, dimension 1 and 3 volumes, probabilities, IID estimates, deterministic seed and parameter rejection.");
