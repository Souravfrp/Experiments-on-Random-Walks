/* Node smoke tests for site/sim_worker.js; no npm dependencies required.
 * This validates seeded browser execution, diagnostic ranges and exact coupon TV.
 * It does not prove equality of the JS, Python and C++ transition kernels.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source=fs.readFileSync(path.join(__dirname,"../site/sim_worker.js"),"utf8");
function execute(params) {
  const messages=[];
  const context=vm.createContext({
    self: {postMessage: value=>messages.push(value)},
    performance: {now: ()=>0}
  });
  vm.runInContext(source,context,{filename:"sim_worker.js",timeout:10000});
  context.self.onmessage({data:params});
  const errors=messages.filter(m=>m.type==="error");
  const done=messages.find(m=>m.type==="done");
  return {errors,done,progress:messages.filter(m=>m.type==="progress")};
}
const input={n:3,steps:32,chains:80,seed:2026,walk:"all"};
const full=execute(input);
assert.equal(full.errors.length,0);
assert.ok(full.done);
assert.equal(full.done.payload.results.length,5);
for(const r of full.done.payload.results){
  assert.equal(r.checkpoints.at(-1).step,input.steps);
  assert.ok(r.acceptance>0&&r.acceptance<=1,r.walk+" acceptance in [0,1]");
  for(const c of r.checkpoints){
    assert.ok(c.ks>=0&&c.ks<=1&&Number.isFinite(c.ks),r.walk+" finite KS");
    assert.ok(c.momentError>=0&&Number.isFinite(c.momentError),r.walk+" finite moment");
  }
  for(const [x,y] of r.endpoints){
    assert.ok(x>=-0.5&&x<=0.5,r.walk+" x within cube");
    assert.ok(y>=-0.5&&y<=0.5,r.walk+" y within cube");
  }
  const isolated=execute({...input,walk:r.walk});
  assert.ok(isolated.done,r.walk+" isolated computation succeeded");
  assert.equal(
    JSON.stringify(isolated.done.payload.results[0].checkpoints),
    JSON.stringify(r.checkpoints),
    r.walk+" stable trajectory across all-walk versus single-walk selection"
  );
}
const coord=execute({n:20,steps:64,chains:100,seed:2026,walk:"coordinate_hit_run"});
assert.ok(coord.done);
assert.ok(Math.abs(coord.done.payload.results[0].exact_coordinate_tv-0.5582308472)<1e-9);
const one=execute({n:1,steps:16,chains:30,seed:2,walk:"coordinate_hit_run"});
assert.equal(one.done.payload.results[0].exact_coordinate_tv,0);
const invalid=execute({n:10000,steps:256,chains:100,seed:2026,walk:"ball"});
assert.equal(invalid.done,undefined);
assert.match(invalid.errors[0].message,/Dimension/);
const overBudget=execute({n:30,steps:2048,chains:1000,seed:1,walk:"all"});
assert.match(overBudget.errors[0].message,/budget/);
console.log("Browser engine smoke tests passed: all five walks, deterministic seeds, exact coordinate TV and safety limits.");
