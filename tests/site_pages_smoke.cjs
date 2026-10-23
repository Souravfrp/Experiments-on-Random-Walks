"use strict";
/* Routing/layout regression checks; the scientific engines have separate tests. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const read=(name)=>fs.readFileSync(path.join(__dirname,"../site",name),"utf8");
const walks=read("index.html"),mixed=read("mixed-volumes.html"),css=read("style.css");
function number(s,fragment){return s.split(fragment).length-1;}
function validatePage(s,title){
 assert.equal(number(s,'class="study-tabs"'),1,title+": exactly one tab bar");
 assert.equal(number(s,'href="./index.html"'),1,title+": links back to the Random Walks page");
 assert.ok(s.includes('href="./mixed-volumes.html"'),title+": links to the mixed-volume page");
 assert.equal(number(s,"<main"),1,title+": one main");
 assert.equal(number(s,"</main>"),1,title+": one main closing tag");
 assert.equal(number(s,"<section"),number(s,"</section>"),title+": balanced sections");
 assert.ok(s.includes('href="./style.css"'),title+": shared site styles");
}
validatePage(walks,"Random Walks");
validatePage(mixed,"Mixed Volumes");
assert.ok(walks.includes('aria-current="page">Experiments on Random Walks'));
assert.ok(mixed.includes('aria-current="page">Approximation of Mixed Volumes'));
assert.ok(walks.includes('id="run-form"'));
assert.ok(walks.includes('id="results"'));
assert.ok(!walks.includes('id="mixed-volume-lab"'));
assert.ok(!walks.includes('src="./mixed_volume.js"'));
assert.ok(mixed.includes('id="mixed-volume-lab"'));
assert.ok(mixed.includes('id="mv-form"'));
assert.ok(mixed.includes('id="mv-output"'));
assert.ok(mixed.includes('src="./mixed_volume.js"'));
assert.ok(!mixed.includes('src="./playground.js"'));
assert.ok(css.includes(".study-tabs"));
assert.ok(walks.includes('location.hash === "#mixed-volume-lab"'),"Redirect bookmarks to old anchor");
console.log("Both standalone experiment pages and cross-navigation passed structural checks.");
