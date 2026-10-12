// Execute the production English search script with a minimal DOM and controlled data.
// Tests real search button wiring, results, and shared verdict selection without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const input = {value:'', addEventListener(){}, focus(){}, select(){}};
const results = {innerHTML:'', addEventListener(){}, contains(){return false}};
const count = {textContent:'', dataset:{}};
const button = {};
const elements = {searchInput:input, searchResults:results, catalogCount:count, searchBtn:button};
const document = {
  getElementById(id){return elements[id] || null},
  querySelectorAll(){return []},
  addEventListener(){},
  activeElement:null
};
const fixture = {
  '../data/plants.json':[{id:'test_leaf',ko:'시험잎',en:'Test Leaf',scientific:'Testus folia',identity_status:'verified'},{id:'test_leaf_duplicate',ko:'시험잎',en:'Test Leaf',scientific:'Testus folia',identity_status:'verified'}],
  '../data/korean_retail_name_map.json':[],
  '../data/public_assessments.json':[{plant_id:'test_leaf',animal_taxon:'Testudo',verdict:'supported_mixed_diet',confidence:'high'},{plant_id:'test_leaf_duplicate',animal_taxon:'Testudo',verdict:'supported_mixed_diet',confidence:'high'}],
  '../data/i18n/en/catalog_en.json':{plants:[{id:'test_leaf',name:'Test Leaf',aliases:['Leaf Test'],why:'Fixture evidence',role:'Mixed diet'},{id:'test_leaf_duplicate',name:'Test Leaf',aliases:[],why:'Fixture evidence',role:'Mixed diet'}]},
  '../data/verified_plant_images_v56.json':{images:[]}
};
const core = require('../verdict-core.js');
const EN = {
  grades:{supported_mixed_diet:{label:'Recommended',meaning:'Mixed diet'}},
  certainty:{high:'High'},
  decision:{A:'Can feed'},
  action:{A:'Mix with other plants'},
  noDefault:{label:'No assessment'},
  hold:{label:'On hold'}
};
const context = {
  window:{TortoiseVerdict:core,TFDB_EN:EN},
  document,
  location:{search:''},
  URLSearchParams,
  setTimeout,
  clearTimeout,
  fetch:async url=>({ok:!!fixture[url],json:async()=>fixture[url]})
};
vm.runInNewContext(fs.readFileSync('en/search-en.js','utf8'),context,{filename:'en/search-en.js'});
async function main(){
  for(let i=0;i<20 && count.dataset.ready!=='1';i++)await new Promise(r=>setTimeout(r,5));
  assert.equal(count.dataset.ready,'1','catalog loaded');
  assert.equal(typeof button.onclick,'function','search button bound');
  input.value='Test Leaf';button.onclick();
  assert.match(results.innerHTML,/data-plant-id="test_leaf"/);
  assert.match(results.innerHTML,/data-grade="A"/);
  assert.equal((results.innerHTML.match(/data-plant-id=/g)||[]).length,1,'duplicate botanical identity appears once');
  input.value='시험잎';button.onclick();
  assert.match(results.innerHTML,/data-plant-id="test_leaf"/,'Korean query searches English catalog');
  input.value='not-in-catalog';button.onclick();
  assert.match(results.innerHTML,/No matching public assessment/);
  console.log('PASS: English search execution, bilingual query, canonical grade, empty result');
}
main().catch(e=>{console.error(e);process.exitCode=1});
