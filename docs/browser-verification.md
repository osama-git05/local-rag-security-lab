# Browser workflow verification

Phase 0 Step 03 checks actual user interactions in the company assistant at `http://127.0.0.1:8001/`. The operator console at port 8010 runs backend suites; a passing suite does not complete this manual browser checklist.

## Batch 1 Employee session and clearing controls

Results distinguish pending checks from owner-reported outcomes. Report actual observations rather than copying expected outcomes as evidence. On 4 November 2026, the owner confirmed that New conversation and Disconnect work and requested that their screenshots be skipped. These are manual reports, not independently automated browser checks.

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| UI-01 | Open the company assistant and connect using the employee token | Employee role is server-verified; connection form closes and the token field is cleared | Pass — verified in Chrome against the live local API on 5 November |
| UI-02 | Ask `How much annual leave do employees receive?` and submit with Enter | A loading state appears, then an answer about 25 days with `policy-leave` and employee-only source metadata | Pass — Enter, pending state and cited live response verified in Chrome on 5 November |
| UI-03 | Click New conversation after the answer finishes | Question/answer history, latest sources and response-time metadata clear; employee account remains connected | Pass — owner-reported; screenshots skipped at owner's request |
| UI-04 | Click the employee Disconnect control | Identity and conversation/source state clear; reconnecting is required to submit another query | Pass — owner-reported; screenshots skipped at owner's request |

Capture the completed employee answer as `docs/screenshots/32-employee-policy-answer.png`, using the existing master-plan checkpoint. Include the role, question, answer and source panel. Hide tokens, clipboard popups and unrelated desktop content. Do not recreate a passing image if the actual result differs.

The owner supplied a cropped answer frame showing the 25-day leave answer and source chips. It does not establish all the session/keyboard/clearing steps above. At the owner's request, the chat renderer now hides inline bracketed references whose IDs match the returned sources, while retaining source chips and the context panel. The API answer still contains its citations and passes the same server-side validation. Refresh the page and reconnect before capturing the updated presentation.

The owner later reported the onboarding tag still visible. The current formatter was checked against the saved onboarding response and correctly removed `ticket-onboarding-injection`. The live script matched disk, but asset routes lacked explicit cache control. The page now uses content-hashed asset URLs and scripts/styles use `Cache-Control: no-store`; live delivery and five UI-route checks passed after API restart. Use Ctrl+Shift+R, reconnect and submit a new question to verify the current renderer. Existing in-memory messages are not retroactively rewritten.

Text results are sufficient for the current manual batches; the owner requested skipping the clearing/disconnect screenshots. A failure should include the action and observed result; preserve it before applying a fix. Do not publish authentication headers or real `.env` contents.

## Batch 2 Employee and administrator document access

Use the company assistant at port 8001, not the operator console. Ask the same question under each verified account:

> When does the finance team review supplier payments, and what approval is needed for payments above 5000 BHD?

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| UI-05 | Connect as employee and ask the finance question | Controlled insufficient-information answer; no restricted finance details or `admin-finance` source | Pass — owner-supplied answer/source frame in requested employee test context; account badge is cropped |
| UI-06 | Disconnect, connect as administrator and ask the same question | Friday payment reviews and two-administrator approval above 5000 BHD, supported by `admin-finance` in the source chips/panel | Pass — owner-supplied answer/source frame in requested administrator test context; account badge is cropped |

Provide each answer and the displayed source IDs as text. An error is a separate outcome to investigate, not a passing refusal. Do not share the tokens. Screenshots are not required for this batch.

The owner supplied two frames in the requested order. The [employee result](screenshots/34-employee-access-boundary.png) shows the canonical insufficient-information answer with `policy-leave` and `ticket-onboarding-injection`, with no `admin-finance` chip. The [administrator result](screenshots/33-admin-finance-answer.png) shows Friday reviews and two-administrator approval above 5000 BHD, with `admin-finance` and `ticket-onboarding-injection` chips. No inline citation tags or credential values are visible.

Roles are assigned from the requested test context, not independently established by the cropped frames. The administrator question includes an extra `1.` line, so these are manual functional smoke checks, not a controlled byte-identical prompt comparison. Source chips show returned documents; they do not prove every returned document supports each claim or expose the complete private model context.

## Batch 3 Invalid token keyboard and reload

Text results are sufficient. The owner reported reload disconnecting the account, supplied a frame showing an unrecognized-token error and subsequently confirmed Shift+Enter works.

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| UI-07 | Disconnect, then attempt to connect with the literal nonfunctional value `invalid-test-token` | Connection rejected with a safe error; no account becomes connected | Pass — rejected-token error visible in owner-supplied frame; exact submitted value is not visible |
| UI-08 | Connect as employee, type draft text and press Shift+Enter | A newline is inserted without submitting the question or starting generation; clear the draft afterwards | Pass — owner-reported; no screenshot requested |
| UI-09 | Reload the page while the employee account is connected | Token/identity and displayed conversation clear; the page requires connecting again | Pass for reconnection requirement — owner reports reload disconnects; complete cleared-state frame not supplied |

Report each outcome as pass/fail and describe any unexpected behavior. Do not provide real token values.

The [rejected-token capture](screenshots/63-invalid-token-rejected.png) shows an empty token field and the safe message “That access token was not recognized. Check your local account token.” It does not itself prove the reload action; that outcome is owner-reported. Reload disconnecting is the intended consequence of keeping the token only in page memory. No persistence change was requested or implemented.

## Later batches

### Batch 4 Clearing during an active request

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| UI-10 | Submit the leave question as employee; while loading, click New conversation | Conversation/sources clear and account stays connected; the old answer does not reappear after the original request could have completed | Pass — owner-reported; no screenshot requested |
| UI-11 | Submit again; while loading, Disconnect | Identity/conversation clear; no old answer or sources appear while disconnected | Pass — owner-reported; no screenshot requested |

Use the normal leave question and act while the loading message is visible. Observe for at least 20 seconds for these local smoke checks; report if an answer reappears. This manual observation window is not proof of every timing condition. Cancelling the browser fetch does not guarantee that a generation already executing on the server stops.

The owner reported that both active-request clearing checks work. This records the observed manual outcome, not proof that the server-side generation was cancelled or every timing interleaving is safe.

### Batch 5 Account switching and narrow layout

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| UI-12 | Connect as administrator, start the finance question, disconnect while loading, then immediately connect as employee and ask the leave question | The prior administrator answer never appears in the employee session; the new answer and sources stay within employee scope | Pass — owner-reported; no screenshot requested |
| UI-13 | Narrow the browser pane and use the account, composer, send and source controls | Content wraps without horizontal page overflow or clipped controls; navigation and reading remain usable | Pass — owner-reported narrow-pane smoke check; no screenshot requested |

For UI-12, observe through completion of the new employee request and for at least 20 seconds overall. Report role labels, any unexpected late answer and source IDs without sharing tokens. For UI-13, a narrow desktop pane is a responsive-layout smoke check, not verification on every mobile device. No screenshots are required.

The owner reported both account switching and narrow layout working. This does not establish every race interleaving or every mobile viewport.

### Batch 6 Local model service unavailable

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| UI-14 | With no workflow/request active, temporarily stop Ollama, keep the API running, and submit the leave question as employee | A friendly service/request failure appears; no partial answer, raw traceback, credentials or filesystem paths are shown; send controls recover | Pass across two checks — real outage API response on 4 November and browser rendering/control recovery with the same 502 body replayed on 5 November |
| UI-15 | Restart the existing Ollama service and repeat the same question | Normal document-grounded answer with permitted sources returns | Pass across two checks — real API recovery on 4 November and a successful live browser retry after the replayed response on 5 November |

Use only the existing local runtime and installed models. Leave the assistant API running so this checks model-service failure rather than loss of the whole web application. Restore Ollama immediately after the failure check. Do not download models, rebuild the index or recreate credentials. A reported error is not an attack-success/defense outcome. Text observations suffice.

At the owner's request, the assistant performed a real stop/restart test while holding the operator workflow lock. The [service check](../results/service-failure-recovery-20261104T195108760811Z.json) records ten passing prerequisite/failure/recovery assertions: the API stayed available, the offline-model query returned the exact safe HTTP 502 body with no partial answer, Ollama was restored, and the same employee query returned a cited 25-day answer. This is API evidence, not a claim that the browser message or send controls were visually checked.

The [first attempt](../results/service-failure-recovery-20261104T194936977996Z.json) stopped at a reachability probe that returned ConnectTimeout rather than ConnectError; its restoration check passed. That incomplete attempt is preserved. The successful retry treated a timed-out probe as unavailable service and retained the application's existing safe status/body expectations. No application source, credentials, corpus, database or model installation was changed. Ollama was running at the end.

## Release browser evidence — 5 November 2026

A separate Chrome session verified employee identity through the live API, dialog closure and token-field clearing. Enter submitted the leave question, displayed the pending state and disabled Send. The live response returned HTTP 200 and the displayed 25-day answer with `policy-leave` and `policy-security` employee sources.

The browser check replayed the same safe HTTP 502 status and body recorded in the 4 November real Ollama outage. The UI displayed the generic error, cleared pending and source state, and restored the composer and Send button. The interception was removed before retrying against the live API. These are separate browser and real outage checks. A single browser session spanning an actual Ollama stop and restart remains unverified.

[Screenshot 71, safe error](screenshots/71-chat-safe-error.png), [screenshot 72, live loading](screenshots/72-chat-loading.png), [screenshot 73, live retry](screenshots/73-chat-live-recovery.png), [browser report](../results/chat-release-browser-20261105T104414614Z.json).
