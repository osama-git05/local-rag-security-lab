"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  let token = "";
  let principal = null;
  let request = null;
  let generation = 0;
  let paymentRequest = null;
  let paymentGeneration = 0;
  const dialog = $("account-dialog");
  const conversation = $("conversation");

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function displayAnswer(answer, sources) {
    const sourceIds = new Set(sources.map((source) => source.document_id));
    // The API retains and validates citations; source chips show them separately.
    return answer.replace(/[ \t]*\[([^\[\]\r\n]+)\]/g, (reference, id) => sourceIds.has(id) ? "" : reference).trim();
  }
  function message(kind, text) {
    const node = element("article", `message ${kind}`);
    const heading = element("div", "message-heading");
    heading.append(element("span", "", kind === "user" ? "↗" : "✧"));
    heading.append(document.createTextNode(kind === "user" ? "YOU" : "EXAMPLECO ASSISTANT"));
    node.append(heading, element("div", "message-body", text));
    conversation.append(node);
    conversation.scrollTop = conversation.scrollHeight;
    return node;
  }
  function resetConversation() {
    resetPayments();
    generation += 1;
    if (request) request.abort();
    request = null;
    conversation.querySelectorAll(".message").forEach((node) => node.remove());
    $("welcome").hidden = false;
    $("sources").replaceChildren(element("p", "sources-empty", "The documents used for your latest answer will appear here."));
    $("answer-meta").textContent = "";
    $("question").value = "";
    setBusy(false);
  }
  function setBusy(busy) {
    $("send-button").disabled = busy;
    $("question").disabled = busy;
    $("composer-status").textContent = busy ? "Finding an answer in your permitted documents…" : principal ? "Each question is answered independently from company documents." : "Connect your account to start a conversation.";
  }
  function updateAccount() {
    $("account-label").textContent = principal ? `${principal.role === "admin" ? "Administrator" : "Employee"} · Disconnect` : "Connect account";
    $("access-title").textContent = principal ? `${principal.role === "admin" ? "Administrator" : "Employee"} access` : "Account not connected";
    $("access-description").textContent = principal ? `${principal.user_id} · ${principal.role === "admin" ? "Employee and administrator documents" : "Employee documents only"}` : "Connect to verify your access.";
    $("finance-suggestion").hidden = principal?.role !== "admin";
    $("payments-form").hidden = principal?.role !== "admin";
    $("payments-access").textContent = principal?.role === "admin" ? "Administrator access · Read-only payment view" : principal ? "Supplier payments are restricted to administrator accounts." : "Connect an administrator account to view supplier payments.";
    setBusy(false);
  }
  function disconnect() {
    token = "";
    principal = null;
    $("access-token").value = "";
    resetConversation();
    updateAccount();
  }
  function showLogin() {
    $("login-error").textContent = "";
    if (!dialog.open) dialog.showModal();
    $("access-token").focus();
  }
  $("account-button").addEventListener("click", () => principal ? disconnect() : showLogin());
  $("close-dialog").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => { $("access-token").value = ""; });
  $("new-chat").addEventListener("click", resetConversation);

  function resetPayments() {
    paymentGeneration += 1;
    if (paymentRequest) paymentRequest.abort();
    paymentRequest = null;
    $("payments-result").replaceChildren();
    $("payments-result").hidden = true;
    $("payments-status").textContent = "";
    $("payments-submit").disabled = false;
  }
  function money(value) {
    const [whole, fraction] = value.split(".");
    return `${BigInt(whole).toLocaleString("en-GB")}.${fraction}`;
  }
  function validatedPayments(data, month) {
    const amount = (value) => typeof value === "string" && /^(0|[1-9][0-9]*)\.[0-9]{3}$/.test(value);
    if (!data || data.operation !== "supplier_payments_above_threshold" || data.month !== month || data.currency !== "BHD" || data.threshold_bhd !== "5000.000" || !Array.isArray(data.rows) || data.rows.length > 1000 || data.row_count !== data.rows.length || !amount(data.total_bhd) || !data.dataset || !/^[a-f0-9]{32}$/.test(data.dataset.version) || !/^[a-f0-9]{64}$/.test(data.dataset.source_sha256) || typeof data.dataset.imported_at_utc !== "string") throw new Error("The payment service returned an unexpected response.");
    let total = 0n;
    const ids = new Set();
    let previous = "";
    for (const row of data.rows) {
      if (!row || typeof row.payment_id !== "string" || !/^[A-Za-z0-9_-]{1,64}$/.test(row.payment_id) || ids.has(row.payment_id) || typeof row.supplier_name !== "string" || typeof row.payment_date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(row.payment_date) || row.payment_date.slice(0, 7) !== month || !amount(row.amount_bhd) || !Number.isInteger(row.source_line) || row.source_line < 2) throw new Error("The payment service returned an unexpected row.");
      const units = BigInt(row.amount_bhd.replace(".", ""));
      const order = `${row.payment_date}/${row.payment_id}`;
      if (units <= 5000000n || order < previous) throw new Error("The payment service returned inconsistent results.");
      ids.add(row.payment_id); previous = order; total += units;
    }
    if (total !== BigInt(data.total_bhd.replace(".", ""))) throw new Error("The payment total does not match its records.");
    const policy = data.policy;
    if (!policy || policy.document_id !== "admin-finance" || policy.access_level !== "admin" || policy.trust_level !== "curated" || typeof policy.source !== "string" || typeof policy.excerpt !== "string" || !policy.excerpt.trim() || typeof policy.dataset_version !== "string" || !/^[a-f0-9]{64}$/.test(policy.source_sha256) || !/^[a-f0-9]{64}$/.test(policy.manifest_sha256) || !Number.isInteger(policy.start_line) || policy.start_line < 1 || !Number.isInteger(policy.end_line) || policy.end_line < policy.start_line) throw new Error("The payment service returned an invalid policy reference.");
    return data;
  }
  function renderPayments(data) {
    const result = $("payments-result");
    const summary = element("div", "payments-summary");
    summary.append(element("div", "", `${data.row_count} qualifying payments`), element("strong", "", `${money(data.total_bhd)} BHD`));
    result.append(summary);
    if (data.rows.length) {
      const wrapper = element("div", "payments-table-wrap");
      wrapper.tabIndex = 0;
      wrapper.setAttribute("role", "region");
      wrapper.setAttribute("aria-label", "Payment records; scroll horizontally on small screens");
      const table = element("table", "payments-table");
      table.append(element("caption", "", `Supplier payments above 5,000 BHD · ${data.month}`));
      const head = element("thead"); const heading = element("tr");
      for (const label of ["Payment", "Supplier", "Date", "Amount (BHD)", "Source line"]) {
        const cell = element("th", "", label); cell.scope = "col"; heading.append(cell);
      }
      head.append(heading); const body = element("tbody");
      for (const row of data.rows) {
        const record = element("tr");
        for (const value of [row.payment_id, row.supplier_name, row.payment_date, money(row.amount_bhd), String(row.source_line)]) record.append(element("td", "", value));
        body.append(record);
      }
      table.append(head, body); wrapper.append(table); result.append(wrapper);
    } else result.append(element("p", "", "No payments above 5,000 BHD were found for this month."));
    const policy = element("section", "payment-policy");
    policy.setAttribute("aria-label", "Payment approval policy");
    policy.append(element("h3", "", "Review & approval policy"), element("blockquote", "", data.policy.excerpt), element("span", "source-chip", data.policy.document_id), element("p", "", "Policy requirements are separate from payment status. These records do not show whether approval was obtained."));
    const policyDetails = element("details");
    policyDetails.append(element("summary", "", "Policy source details"), element("p", "", `${data.policy.source} · lines ${data.policy.start_line}–${data.policy.end_line} · corpus ${data.policy.dataset_version}`), element("p", "", `Source SHA-256: ${data.policy.source_sha256}`), element("p", "", `Manifest SHA-256: ${data.policy.manifest_sha256}`));
    policy.append(policyDetails); result.append(policy);
    const provenance = element("details", "payment-provenance");
    provenance.append(element("summary", "", "Dataset & calculation details"), element("p", "", `Dataset version: ${data.dataset.version}`), element("p", "", `Source SHA-256: ${data.dataset.source_sha256}`), element("p", "", `Imported: ${data.dataset.imported_at_utc}`), element("p", "", "Total is the exact sum of the displayed records. This view does not establish whether a payment received approval."));
    result.append(provenance); result.hidden = false;
  }
  $("payments-month").addEventListener("change", resetPayments);
  $("payments-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (principal?.role !== "admin" || paymentRequest) return;
    const month = $("payments-month").value;
    if (!/^[0-9]{4}-[0-9]{2}$/.test(month)) return;
    resetPayments();
    const current = paymentGeneration;
    const controller = new AbortController(); paymentRequest = controller;
    const timeout = setTimeout(() => controller.abort(), 20000);
    $("payments-submit").disabled = true;
    $("payments-status").textContent = "Loading permitted payment records…";
    try {
      const response = await fetch("/payments/query", {method: "POST", headers: {"Content-Type": "application/json", Authorization: `Bearer ${token}`}, body: JSON.stringify({operation: "supplier_payments_above_threshold", month}), signal: controller.signal, cache: "no-store"});
      if (current !== paymentGeneration) return;
      if (response.status === 401) { disconnect(); showLogin(); $("login-error").textContent = "Your account could not be verified. Connect again."; return; }
      const errors = {403: "Your account cannot access supplier payments.", 422: "Select a valid payment month.", 503: "Payment data is unavailable. Ask your administrator to check the active dataset."};
      if (!response.ok) throw new Error(errors[response.status] || "Could not load payments. Please try again.");
      const data = validatedPayments(await response.json(), month);
      if (current !== paymentGeneration) return;
      renderPayments(data);
      $("payments-status").textContent = `Showing ${month} · Payments strictly above 5,000 BHD`;
    } catch (error) {
      if (current !== paymentGeneration) return;
      $("payments-result").replaceChildren(); $("payments-result").hidden = true;
      $("payments-status").textContent = error.name === "AbortError" ? "The payment request timed out. Please try again." : error instanceof TypeError ? "Could not reach the payment service. Check the local server." : error.message;
    } finally {
      clearTimeout(timeout);
      if (current === paymentGeneration) { paymentRequest = null; $("payments-submit").disabled = false; }
    }
  });

  $("account-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const supplied = $("access-token").value.trim();
    $("access-token").value = "";
    $("connect-button").disabled = true;
    $("login-error").textContent = "";
    try {
      const response = await fetch("/whoami", {headers: {Authorization: `Bearer ${supplied}`}, cache: "no-store", signal: AbortSignal.timeout(15000)});
      if (response.status === 401) throw new Error("That access token was not recognized. Check your local account token.");
      if (!response.ok) throw new Error("Could not verify your account. Check that the local server is available.");
      const identity = await response.json();
      if (!["employee", "admin"].includes(identity.role) || typeof identity.user_id !== "string") throw new Error("The server returned an unexpected account response.");
      if (!dialog.open) return;
      token = supplied;
      principal = identity;
      resetConversation();
      updateAccount();
      dialog.close();
      $("question").focus();
    } catch (error) {
      $("login-error").textContent = error.name === "TimeoutError" || error instanceof TypeError ? "Could not reach the local server. Check that it is running." : error.message;
    } finally {
      $("connect-button").disabled = false;
    }
  });

  document.querySelectorAll(".suggestion").forEach((button) => button.addEventListener("click", () => {
    $("question").value = button.dataset.question;
    if (!principal) showLogin(); else $("question").focus();
  }));
  $("question").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      $("question-form").requestSubmit();
    }
  });
  $("question-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (request) return;
    if (!principal) { showLogin(); return; }
    const question = $("question").value.trim();
    if (!question || question.length > 4000) return;
    const current = generation;
    const controller = new AbortController();
    request = controller;
    // The server may embed and generate sequentially, each with a finite timeout.
    const timeout = setTimeout(() => controller.abort(), 390000);
    $("welcome").hidden = true;
    message("user", question);
    $("question").value = "";
    const pending = message("pending", "Looking through your company knowledge…");
    setBusy(true);
    const started = performance.now();
    try {
      const response = await fetch("/query", {method: "POST", headers: {"Content-Type": "application/json", Authorization: `Bearer ${token}`}, body: JSON.stringify({question}), signal: controller.signal, cache: "no-store"});
      if (current !== generation) return;
      if (response.status === 401) { disconnect(); showLogin(); $("login-error").textContent = "Your account could not be verified. Connect again."; return; }
      const errors = {403: "Your account is not permitted to access these documents.", 422: "Check your question. Use between 1 and 4000 characters.", 502: "I couldn’t produce a validated answer. Try rephrasing your question or ask the relevant team.", 504: "The local model took too long to respond. Please try again."};
      if (!response.ok) throw new Error(errors[response.status] || "The assistant is unavailable. Please try again later.");
      const data = await response.json();
      if (typeof data.answer !== "string" || !Array.isArray(data.sources) || data.sources.some((source) => typeof source.document_id !== "string" || typeof source.source !== "string" || !["employee", "admin"].includes(source.access_level))) throw new Error("The assistant returned an unexpected response. Please try again.");
      pending.remove();
      const answer = message("assistant", displayAnswer(data.answer, data.sources));
      const chips = element("div", "source-chips");
      $("sources").replaceChildren();
      for (const source of data.sources) {
        chips.append(element("span", "source-chip", source.document_id));
        const record = element("div", "source-record");
        record.append(element("strong", "", source.document_id), element("small", "", `${source.source} · ${source.access_level}`));
        $("sources").append(record);
      }
      if (data.sources.length) answer.append(chips);
      else $("sources").append(element("p", "sources-empty", "No source documents accompanied this answer."));
      $("answer-meta").textContent = `Local response · ${((performance.now() - started) / 1000).toFixed(1)} s`;
    } catch (error) {
      if (current !== generation) return;
      pending.remove();
      message("error", error.name === "AbortError" ? "The request timed out. Please try again." : error instanceof TypeError ? "Could not reach the local server. Check that it is running." : error.message);
      $("sources").replaceChildren(element("p", "sources-empty", "No validated answer was returned for this request."));
      $("answer-meta").textContent = "";
    } finally {
      clearTimeout(timeout);
      if (current === generation) {
        request = null;
        setBusy(false);
        $("question").focus();
        conversation.scrollTop = conversation.scrollHeight;
      }
    }
  });
})();
