"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  let token = "", selected = null, timer = null, epoch = 0, running = false;
  const node = (tag, text, className) => { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (className) el.className = className; return el; };
  const badge = (status) => node("span", status.toUpperCase(), `status ${status}`);
  function disconnect() {
    token = ""; selected = null; epoch++; clearTimeout(timer); running = false;
    $("workspace").hidden = true; $("sign-in").hidden = false; $("token").value = "";
    $("account").textContent = "Connect administrator";
    for (const id of ["readiness", "run-details", "stages", "cases", "history"]) $(id).replaceChildren();
    $("download").hidden = true; $("notice").textContent = "Disconnected. Active server-side tests continue and their reports remain available after reconnecting.";
    enableActions();
  }
  function enableActions() { document.querySelectorAll("[data-suite]").forEach((button) => { button.disabled = running; }); }
  async function api(path, options = {}) {
    const activeEpoch = epoch;
    const response = await fetch(path, {...options, cache:"no-store", signal:AbortSignal.timeout(45000), headers:{Authorization:`Bearer ${token}`, "Content-Type":"application/json", "X-Lab-Console":"1", ...(options.headers || {})}});
    if (activeEpoch !== epoch) throw new Error("Account changed.");
    if (response.status === 401) { disconnect(); throw new Error("Connect your administrator account again."); }
    const body = await response.json();
    if (activeEpoch !== epoch) throw new Error("Account changed.");
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The requested action was rejected.");
    return body;
  }
  function errorNotice(error) { if (token) $("notice").textContent = error.name === "TimeoutError" || error instanceof TypeError ? "Could not reach the console. The server-side run may still be active; reconnect before retrying." : error.message; }
  async function refreshReadiness() {
    $("refresh").disabled = true;
    try {
      const result = await api("/api/readiness");
      $("readiness").replaceChildren(...result.checks.map((check) => { const el=node("div",undefined,"readiness-item");el.append(badge(check.status),node("strong",check.label),node("p",check.message));return el; }));
    } catch (error) { errorNotice(error); }
    finally { $("refresh").disabled = false; }
  }
  function renderReport(report) {
    $("run-status").replaceWith(Object.assign(badge(report.status), {id:"run-status"}));
    $("run-details").replaceChildren(node("p", `${report.suite} · ${report.run_id}`, "run-meta"));
    if (report.message) $("run-details").append(node("p", report.message));
    if (report.case_counts) $("run-details").append(node("div", `${report.case_counts.pass} passed · ${report.case_counts.fail} failed · ${report.case_counts.error} errors`, "counts"));
    for (const [label,value] of [["Snapshot", report.environment_snapshot], ["Case report", report.evaluation_report]]) if (value) $("run-details").append(node("p", `${label}: ${value}`, "run-meta"));
    if (report.elapsed_ms != null) $("run-details").append(node("p", `Workflow time: ${(report.elapsed_ms/1000).toFixed(1)} s · Stage counts and case counts are separate.`, "run-meta"));
    $("stages").replaceChildren(...report.stages.map((stage) => { const el=node("div",undefined,"stage"), content=node("div"); content.append(node("strong",stage.name)); if (stage.message) content.append(node("small",stage.message)); if (stage.elapsed_ms!=null) content.append(node("small",`${(stage.elapsed_ms/1000).toFixed(1)} s`));el.append(content,badge(stage.status));return el; }));
    $("cases").replaceChildren(...(report.cases || []).map((item) => { const el=node("div",undefined,"case"),content=node("div");content.append(node("strong",item.case_id));content.append(node("small",`HTTP ${item.status ?? "unavailable"} · ${item.elapsed_ms == null ? "no timing" : (item.elapsed_ms/1000).toFixed(2)+" s"}`)); if (item.failed_checks.length) content.append(node("small","Failed checks: "+item.failed_checks.join(", ")));if(item.error_type)content.append(node("small",item.error_type));el.append(content,badge(item.outcome));return el; }));
    $("download").hidden = false;
  }
  async function selectRun(id) {
    selected = id; clearTimeout(timer); const requested = id;
    try {
      const report = await api(`/api/runs/${id}`);
      if (selected !== requested) return;
      renderReport(report);
      if (report.status === "running") timer=setTimeout(() => selectRun(requested),2000);
      else await refreshHistory(false);
    } catch (error) { errorNotice(error); }
  }
  async function refreshHistory(selectActive = true) {
    const result = await api("/api/runs");
    running = result.runs.some((report) => report.status === "running");enableActions();
    $("history").replaceChildren(...result.runs.map((report) => { const button=node("button",`${report.suite} · ${report.status.toUpperCase()}`);button.append(node("small",`${report.run_id} · ${report.started_at_utc}`));button.addEventListener("click",()=>selectRun(report.run_id));return button; }));
    if (!result.runs.length) $("history").append(node("p","No workflow reports yet.","muted"));
    if (selectActive) { const active=result.runs.find((report)=>report.status==="running") || result.runs[0];if(active)await selectRun(active.run_id); }
  }
  $("login").addEventListener("submit",async(event)=>{
    event.preventDefault();token=$("token").value.trim();$("token").value="";epoch++;$("connect").disabled=true;
    try { const identity=await api("/api/session");$("sign-in").hidden=true;$("workspace").hidden=false;$("account").textContent=`${identity.user_id} · Disconnect`;$("notice").textContent="Administrator verified. Choose a workflow or review a retained result.";await refreshHistory();await refreshReadiness(); }
    catch(error){token="";$("notice").textContent=error.message;}
    finally{$("connect").disabled=false;}
  });
  $("account").addEventListener("click",()=>token?disconnect():$("token").focus());
  $("refresh").addEventListener("click",refreshReadiness);
  document.querySelectorAll("[data-suite]").forEach((button)=>button.addEventListener("click",async()=>{
    running=true;enableActions();$("notice").textContent="Starting the selected workflow…";
    try{const run=await api("/api/runs",{method:"POST",body:JSON.stringify({suite:button.dataset.suite})});$("notice").textContent="Workflow running. Stages update as each script completes; live generation can take several minutes.";await selectRun(run.run_id);}
    catch(error){errorNotice(error);try{await refreshHistory();}catch(_){} }
  }));
  $("download").addEventListener("click",async()=>{
    if(!selected)return;
    try{const report=await api(`/api/runs/${selected}/download`);const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:"application/json"}));const link=node("a");link.href=url;link.download=`lab-summary-${selected}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){errorNotice(error);}
  });
})();
