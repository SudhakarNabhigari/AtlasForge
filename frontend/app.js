const $ = (id) => document.getElementById(id);
let currentRecord = null;
let activePane = "text";
const api = async (url, options={}) => {
  const response = await fetch(url, options);
  const data = await response.json().catch(()=>({detail:"Server returned an invalid response."}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
};
function toast(message){const el=$("toast");el.textContent=message;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),3000)}
function setBusy(busy){$("extractBtn").disabled=busy;$("extractBtn").innerHTML=busy?"Extracting…":"✦ Extract research <span>→</span>"}
function showLibrary(show){
  $("workspace").classList.toggle("hidden",show);$("library").classList.toggle("hidden",!show);
  $("navNew").classList.toggle("active",!show);$("navLibrary").classList.toggle("active",show);
  $("pageTitle").textContent=show?"Knowledge library":"Research navigator";
  if(show) loadLibrary();
}
$("navNew").onclick=()=>showLibrary(false);
$("navLibrary").onclick=()=>showLibrary(true);
$("tabText").onclick=()=>{activePane="text";$("tabText").classList.add("selected");$("tabFile").classList.remove("selected");$("textPane").classList.remove("hidden");$("filePane").classList.add("hidden")};
$("tabFile").onclick=()=>{activePane="file";$("tabFile").classList.add("selected");$("tabText").classList.remove("selected");$("filePane").classList.remove("hidden");$("textPane").classList.add("hidden")};
$("sourceText").addEventListener("input",()=>{$("charCount").textContent=`${$("sourceText").value.length.toLocaleString()} characters`});
$("fileInput").onchange=()=>{$("fileName").textContent=$("fileInput").files[0]?.name||"No file selected"};
$("clearBtn").onclick=()=>{ $("sourceText").value="";$("charCount").textContent="0 characters";$("fileInput").value="";$("fileName").textContent="No file selected";currentRecord=null;$("resultContent").classList.add("hidden");$("emptyState").classList.remove("hidden");$("validationBadge").textContent="AWAITING INPUT";$("validationBadge").classList.remove("valid");$("saveStatus").textContent=""};
$("extractBtn").onclick=async()=>{
  setBusy(true);$("saveStatus").textContent="";
  try{
    let result;
    if(activePane==="file"){
      const file=$("fileInput").files[0];if(!file)throw new Error("Choose a TXT or MD file first.");
      const form=new FormData();form.append("file",file);
      result=await api("/api/upload",{method:"POST",body:form});
    }else{
      const text=$("sourceText").value.trim();if(text.length<20)throw new Error("Enter at least 20 characters of research text.");
      result=await api("/api/extract",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
    }
    currentRecord={...result.record,id:null};renderResult(currentRecord);
    $("validationBadge").textContent="✓ SCHEMA VALIDATED";$("validationBadge").classList.add("valid");
    toast(result.ai_mode==="gemini"?"AI extraction complete. Review the fields.":"Extraction complete using local fallback. Review the fields.");
  }catch(e){toast(e.message);$("saveStatus").textContent=e.message;$("saveStatus").classList.add("error")}
  finally{setBusy(false)}
};
function lines(value){return Array.isArray(value)?value.join("\n"):""}
function renderResult(r){
  $("emptyState").classList.add("hidden");$("resultContent").classList.remove("hidden");
  $("fieldTitle").value=r.title||"";$("fieldSummary").value=r.summary||"";
  $("fieldClaims").value=lines(r.claims);$("fieldMethods").value=lines(r.methods);
  $("fieldLimitations").value=lines(r.limitations);$("fieldQuestions").value=lines(r.research_questions);
  $("fieldKeywords").value=(r.keywords||[]).join(", ");
  $("saveBtn").classList.toggle("hidden",!!r.id);$("updateBtn").classList.toggle("hidden",!r.id);
  $("saveStatus").classList.remove("error");$("saveStatus").textContent="";
}
function readForm(){
  const title=$("fieldTitle").value.trim();if(!title)throw new Error("Research title is required.");
  const list=(id)=>$(id).value.split("\n").map(x=>x.trim()).filter(Boolean).slice(0,20);
  return {title,summary:$("fieldSummary").value.trim(),claims:list("fieldClaims"),methods:list("fieldMethods"),
    limitations:list("fieldLimitations"),research_questions:list("fieldQuestions"),
    keywords:$("fieldKeywords").value.split(",").map(x=>x.trim()).filter(Boolean).slice(0,20),
    source_text:currentRecord?.source_text||""};
}
$("saveBtn").onclick=async()=>{try{const data=await api("/api/records",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(readForm())});currentRecord=data.record;renderResult(currentRecord);$("saveStatus").textContent="✓ Saved to database.";toast("Research record saved.");await updateCount()}catch(e){$("saveStatus").textContent=e.message;$("saveStatus").classList.add("error")}};
$("updateBtn").onclick=async()=>{try{if(!currentRecord?.id)throw new Error("Open a saved record first.");const data=await api(`/api/records/${currentRecord.id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(readForm())});currentRecord=data.record;renderResult(currentRecord);$("saveStatus").textContent="✓ Record updated in database.";toast("Research record updated.");await updateCount()}catch(e){$("saveStatus").textContent=e.message;$("saveStatus").classList.add("error")}};
async function updateCount(){try{const data=await api("/api/records");$("recordCount").textContent=data.records.length}catch{}}
async function loadLibrary(){
  const q=$("searchInput").value.trim();const list=$("libraryList");list.innerHTML='<div class="no-records">Loading records…</div>';
  try{
    const data=await api("/api/records"+(q?"?q="+encodeURIComponent(q):""));$("recordCount").textContent=data.records.length;
    if(!data.records.length){list.innerHTML='<div class="no-records">No saved records yet. Extract research and save it to build your library.</div>';return}
    list.innerHTML=data.records.map(r=>`<article class="record-card"><h3>${esc(r.title)}</h3><p>${esc((r.summary||"No summary available").slice(0,260))}${(r.summary||"").length>260?"…":""}</p><div class="chips">${(r.keywords||[]).slice(0,5).map(k=>`<span>${esc(k)}</span>`).join("")}</div><div class="record-meta">${esc(new Date(r.updated_at).toLocaleString())} · ${(r.claims||[]).length} claims</div><div class="card-actions"><button class="btn btn-quiet" onclick="openRecord(${r.id})">Open / edit</button><button class="btn btn-quiet" onclick="deleteRecord(${r.id})">Delete</button></div></article>`).join("");
  }catch(e){list.innerHTML=`<div class="no-records">${esc(e.message)}</div>`}
}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
window.openRecord=async(id)=>{try{const data=await api(`/api/records/${id}`);currentRecord=data.record;renderResult(currentRecord);$("validationBadge").textContent="SAVED RECORD";$("validationBadge").classList.add("valid");showLibrary(false)}catch(e){toast(e.message)}};
window.deleteRecord=async(id)=>{if(!confirm("Delete this research record permanently?"))return;try{await api(`/api/records/${id}`,{method:"DELETE"});toast("Record deleted.");loadLibrary();updateCount()}catch(e){toast(e.message)}};
$("searchBtn").onclick=loadLibrary;$("searchInput").addEventListener("keydown",e=>{if(e.key==="Enter")loadLibrary()});
(async()=>{try{const h=await api("/api/health");$("apiStatus").textContent=h.ai_mode==="gemini"?"Gemini AI connected":"API online · local AI fallback";}catch{$("apiStatus").textContent="API unavailable — start backend"}await updateCount()})();
