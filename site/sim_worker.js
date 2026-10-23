/* Browser-only reproduction of the five cube transition rules.
 * Independently implemented in JavaScript. Not a Python/C++ benchmark.
 * All chains start at the origin; the target is uniform on (-1/2,1/2)^n.
 * The exact proposal/acceptance mathematics follows baseline/python/walks.py.
 */
"use strict";
const WALKS = ["ball", "dikin", "coordinate_hit_run", "random_hit_run", "john"];

function generator(seed) {
  // Mulberry32: transparent seeded pseudorandom generator, not cryptographic.
  let state = seed >>> 0, spare = null;
  function uniform() {
    state = (state + 0x6D2B79F5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  function normal() {
    if (spare !== null) {
      const v = spare;
      spare = null;
      return v;
    }
    const u = Math.max(uniform(), Number.MIN_VALUE);
    const r = Math.sqrt(-2 * Math.log(u));
    const a = 2 * Math.PI * uniform();
    spare = r * Math.sin(a);
    return r * Math.cos(a);
  }
  return {uniform, normal};
}

function uniformBall(n, rng, u) {
  let sum = 0;
  do {
    sum = 0;
    for (let i = 0; i < n; i++) {
      u[i] = rng.normal();
      sum += u[i] * u[i];
    }
  } while (sum === 0);
  const scale = Math.pow(rng.uniform(), 1 / n) / Math.sqrt(sum);
  for (let i = 0; i < n; i++) u[i] *= scale;
}

function transition(x, offset, n, walk, rng, u, y) {
  if (walk === "coordinate_hit_run") {
    const i = Math.floor(rng.uniform() * n);
    x[offset + i] = rng.uniform() - 0.5;
    return 1;
  }
  if (walk === "random_hit_run") {
    let squared;
    do {
      squared = 0;
      for (let i = 0; i < n; i++) {
        const z = rng.normal();
        u[i] = z;
        squared += z * z;
      }
    } while (squared === 0);
    let left = -Infinity, right = Infinity;
    for (let i = 0; i < n; i++) {
      const di = u[i];
      if (Math.abs(di) < 1e-15) continue;
      const xi = x[offset + i], a = (-0.5 - xi) / di, b = (0.5 - xi) / di;
      left = Math.max(left, Math.min(a, b));
      right = Math.min(right, Math.max(a, b));
    }
    const t = left + (right - left) * rng.uniform();
    for (let i = 0; i < n; i++) {
      x[offset + i] += t * u[i];
    }
    return 1;
  }

  uniformBall(n, rng, u);
  if (walk === "ball") {
    const delta = 0.8 / Math.sqrt(n);
    for (let i = 0; i < n; i++) {
      const z = x[offset + i] + delta * u[i];
      if (!(z > -0.5 && z < 0.5)) return 0;
      y[i] = z;
    }
    for (let i = 0; i < n; i++) x[offset + i] = y[i];
    return 1;
  }

  if (walk === "dikin") {
    for (let i = 0; i < n; i++) {
      const v = x[offset + i];
      const hx = 1 / ((0.5-v)*(0.5-v)) + 1 / ((0.5+v)*(0.5+v));
      const z = v + u[i] / Math.sqrt(hx);
      if (!(z > -0.5 && z < 0.5)) return 0;
      y[i] = z;
    }
    let reverse = 0, ratio = 0;
    for (let i = 0; i < n; i++) {
      const xi = x[offset+i], yi = y[i];
      const hx = 1 / ((0.5-xi)*(0.5-xi)) + 1 / ((0.5+xi)*(0.5+xi));
      const hy = 1 / ((0.5-yi)*(0.5-yi)) + 1 / ((0.5+yi)*(0.5+yi));
      reverse += hy * (yi-xi)*(yi-xi);
      ratio += 0.5 * Math.log(hy / hx);
    }
    if (reverse > 1 + 1e-11 || Math.log(Math.max(rng.uniform(), 1e-300)) > Math.min(0, ratio)) return 0;
    for (let i = 0; i < n; i++) x[offset + i] = y[i];
    return 1;
  }

  if (walk === "john") {
    for (let i = 0; i < n; i++) {
      const xi = x[offset+i];
      const z = xi + 0.8 * (0.5-Math.abs(xi)) * u[i];
      if (!(z > -0.5 && z < 0.5)) return 0;
      y[i] = z;
    }
    let reverse = 0, ratio = 0;
    for (let i = 0; i < n; i++) {
      const xi = x[offset+i], yi = y[i];
      const dx = 0.5 - Math.abs(xi), dy = 0.5 - Math.abs(yi);
      reverse += ((yi - xi) / dy) ** 2;
      ratio += Math.log(dx / dy);
    }
    if (reverse > 0.64 + 1e-11 || Math.log(Math.max(rng.uniform(), 1e-300)) > Math.min(0, ratio)) return 0;
    for (let i = 0; i < n; i++) x[offset+i] = y[i];
    return 1;
  }
  throw new Error("Unrecognized walk " + walk);
}

function uniformCdf(x) {
  return Math.max(0, Math.min(1, x + 0.5));
}
function triangularCdf(z) {
  if (z <= -1) return 0;
  if (z >= 1) return 1;
  return z < 0 ? 0.5 * (z+1)**2 : 1-0.5*(1-z)**2;
}
function ks(values, cdf) {
  values.sort((a, b) => a-b);
  let k = 0;
  for (let i=0; i<values.length; i++) {
    const f = cdf(values[i]);
    k = Math.max(k, Math.abs(f-i/values.length), Math.abs((i+1)/values.length-f));
  }
  return k;
}
function diagnose(states, n, chains) {
  let maxKs = 0, pairKs = 0, squares = 0;
  const values = new Array(chains);
  for(let i=0; i<n; i++) {
    for(let c=0; c<chains; c++) {
      const v = states[c*n+i];
      values[c]=v;
      squares += v*v;
    }
    maxKs = Math.max(maxKs, ks(values, uniformCdf));
  }
  if(n > 1) {
    const pairs = n===2 ? [[0,1]] : [[0,1],[1,2],[2,0]];
    for(const [i,j] of pairs) {
      for(let c=0; c<chains; c++) values[c]=states[c*n+i]+states[c*n+j];
      pairKs = Math.max(pairKs, ks(values, triangularCdf));
    }
  }
  maxKs = Math.max(maxKs,pairKs);
  const momentError = Math.abs(squares/(n*chains)-1/12)/(1/12);
  return {ks:maxKs, pairKs, momentError};
}
function couponTv(n, t) {
  let probabilities = new Float64Array(n+1);
  probabilities[0] = 1;
  for(let step=0; step<t; step++) {
    const next = new Float64Array(n+1);
    for(let k=0; k<=n; k++) {
      next[k] += probabilities[k]*k/n;
      if(k<n) next[k+1] += probabilities[k]*(n-k)/n;
    }
    probabilities = next;
  }
  return Math.max(0,1-probabilities[n]);
}
function checked(p) {
  const n=Number(p.n), steps=Number(p.steps), chains=Number(p.chains), seed=Number(p.seed);
  if(!Number.isSafeInteger(n)||n<1||n>30)throw new Error("Dimension must be an integer from 1 to 30.");
  if(!Number.isSafeInteger(steps)||steps<16||steps>2048)throw new Error("Steps must be an integer from 16 to 2048.");
  if(!Number.isSafeInteger(chains)||chains<30||chains>1000)throw new Error("Chains must be an integer from 30 to 1000.");
  if(!Number.isSafeInteger(seed)||seed<0||seed>4294967295)throw new Error("Seed must be an integer from 0 to 4,294,967,295.");
  if(p.walk!=="all"&&!WALKS.includes(p.walk))throw new Error("Unknown random walk.");
  const count=p.walk==="all"?5:1;
  if(n*steps*chains*count>8000000)throw new Error("This experiment exceeds the browser safety budget. Reduce dimension, steps, chains, or choose a single walk.");
  return {n,steps,chains,seed,walk:p.walk,count};
}
function run(p) {
  const selected=p.walk==="all"?WALKS:[p.walk], results=[];
  for(let w=0; w<selected.length; w++) {
    const walk=selected[w];
    const rng=generator((p.seed + Math.imul(0x9e3779b9,w+1))>>>0);
    const states=new Float64Array(p.chains*p.n), u=new Float64Array(p.n), y=new Float64Array(p.n);
    const checkpoints=[], clock=performance.now();
    let accepted=0, previousPass=false, proxy=null, elapsed=0;
    for(let t=1; t<=p.steps; t++) {
      for(let c=0; c<p.chains; c++) accepted+=transition(states,c*p.n,p.n,walk,rng,u,y);
      if ((t & (t-1))===0 || t===p.steps) {
        const metric=diagnose(states,p.n,p.chains);
        const pass=metric.ks<=0.15 && metric.momentError<=0.25;
        if(proxy===null && previousPass && pass)proxy=t;
        previousPass=pass;
        checkpoints.push({step:t,...metric,acceptance:accepted/(t*p.chains)});
        elapsed=performance.now()-clock;
        self.postMessage({type:"progress",walk,index:w+1,total:selected.length,step:t,steps:p.steps});
      }
    }
    const endpoints=[];
    // Deterministic representative subset, bounded for plotting.
    const stride=Math.max(1,Math.floor(p.chains/500));
    for(let c=0;c<p.chains;c+=stride){
      const o=c*p.n;endpoints.push([states[o],p.n>=2?states[o+1]:null]);
    }
    results.push({walk,elapsed_ms:elapsed,acceptance:accepted/(p.steps*p.chains),
      proxy_steps:proxy,checkpoints,endpoints,
      exact_coordinate_tv:p.walk==="coordinate_hit_run"||walk==="coordinate_hit_run"?couponTv(p.n,p.steps):null});
    self.postMessage({type:"partial",result:results[results.length-1],index:w+1,total:selected.length});
  }
  return {parameters:p,engine:"Browser JavaScript (independent implementation, Mulberry32 + Box-Muller)",results};
}
self.onmessage=function(event) {
  try {
    const p=checked(event.data);
    self.postMessage({type:"start",parameters:p});
    self.postMessage({type:"done",payload:run(p)});
  } catch(error) {
    self.postMessage({type:"error",message:error.message||String(error)});
  }
};
