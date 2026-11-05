# Supplier-payment interface and evidence

Implemented and verified on 4 November 2026. This is a synthetic local development feature, not a held-out benchmark or general security guarantee.

## Current policy milestone

The combined payment-and-policy view is now implemented. See [policy controls, screenshots 68–69 and current browser results](payment-policy.md). The original frontend verification record below remains historical: its 12-case report predates the policy adapter; the newer browser report passes 14 cases.

## Use the view

1. Open the existing company assistant at `http://127.0.0.1:8001/` and reload to obtain the current assets. Reloading clears the account token and prior results.
2. Connect with the existing administrator account, then scroll below the conversation to **Supplier payments**.
3. Select **October 2026** and click **View payments**. The active golden fixture returns `PAY-001`, `PAY-003`, `PAY-004` and **18,750.125 BHD**. Expand **Dataset & calculation details** to inspect version, file hash and import time. Source-line numbers identify original CSV records.
4. Select **December 2026** to see zero qualifying payments and **0.000 BHD**.
5. Disconnect and connect as an employee. The form and prior finance results disappear; the view explains that administrator access is required. The API independently enforces HTTP 403 even if someone bypasses the hidden form.

The view displays the approved structured operation from `/payments/query`; it makes no model request. Changing the month clears stale results. New conversation, Disconnect, account changes and reload clear payment results; pending responses cannot restore data after disconnect. Service errors clear prior results and restore the button. Supplier names use text rendering, and the browser checks that the total equals the displayed rows using exact integer arithmetic.

The table scrolls horizontally on narrow screens. The mobile screenshot shows the initial left-hand table position; date/amount/source columns remain reachable through horizontal scrolling. Keyboard users can focus the labelled table region. This is one tested 390-pixel viewport, not a claim of coverage for all devices or assistive technologies.

## Numbered screenshots

These are genuine component screenshots from a separate headless Chrome session against the existing API at port 8001. They were visually reviewed. They show fictional records and no credentials, token input, private paths or unrelated browser tabs. They are not captures of the owner's in-app browser.

| File | Observed evidence |
| --- | --- |
| [64 — Administrator payment results](screenshots/64-admin-payment-results.png) | Three October rows, exact total, source lines and expanded dataset provenance |
| [65 — Empty month](screenshots/65-payments-empty-month.png) | December query, zero rows, exact zero total |
| [66 — Employee boundary](screenshots/66-employee-payment-boundary.png) | Administrator-only notice; no form, records, count, total or dataset metadata |
| [67 — Narrow-screen view](screenshots/67-payments-mobile-view.png) | Month selector and total at 390 pixels, with a horizontally scrollable table |

The repeat verification retained timestamped variants of all four images. Their SHA-256 values exactly match the reviewed base images; neither run overwrote earlier evidence. The final report maps each variant to its case and hash. Earlier screenshots 1–63 remain preserved; their prior review limitations still apply.

## Checks actually run

- JavaScript syntax check: passed.
- Existing five UI route/security checks: passed.
- Full isolated workflow: **112 passed**, exit 0; [workflow report](../results/lab-workflow-20261104T202208590595Z-4738ba22.json).
- Real-browser development verification: **12 passed, 0 failed, 0 errors**; [case report](../results/payment-ui-verification-20261104T202147653Z.json).
- Fresh [environment snapshot](../results/environment-20261104T202223012020Z.json): all 45 Python source hashes and six application/console asset hashes matched after checks. It was captured after the browser run, and associated only after verifying unchanged source/assets and driver/fixture hashes. The report records that order explicitly.

Eight browser cases exercise the real local API or real browser state: signed-out access, administrator fixture, empty month, narrow viewport, employee account switch plus actual API denial, reload, month change and New conversation. Four further cases deliberately simulate a 503 response, supplier markup, an inconsistent total and a delayed response during disconnect. These simulations test frontend behavior; they are not claims of a real service outage or corrupted production data. No screenshots of simulated responses were saved.

The report includes per-case durations, outcomes, failed checks, active payment version/hash, screenshot paths/hashes and hashes of the driver, fixture and frontend. Existing API case records and historical reports remain intact. No corpus, credentials, models or Chroma index was rebuilt or replaced. The earlier extended LLM run predates these frontend additions and was not repeated for this deterministic UI batch.

## Reproduce the browser checks

The optional live test requires an existing API on port 8001, the known eight-row fixture already active, existing employee/admin credentials, Node, Playwright and installed Chrome. It reads credentials privately from root `.env` into the child process environment; it does not print them or save browser traces/storage state. It never installs software or downloads a browser. It uses a separate browser context and closes it afterwards.

With those dependencies already available:

```powershell
.venv\Scripts\python.exe -m tests.live.check_payment_ui
```

The session used existing bundled Node and Playwright. Set `--node` and `--node-modules` when using an installation outside the default search path. Run the isolated workflow and environment capture separately:

```powershell
.venv\Scripts\python.exe -m scripts.lab_console --suite isolated
.venv\Scripts\python.exe -m scripts.capture_environment
```

The bundled dependency paths are machine-specific; use your installed Node/module locations elsewhere. The browser check remains explicitly separate from isolated/model-free checks. Its assertions require the golden active dataset; different legitimate business data will fail this known-fixture check. Screenshot filenames gain a timestamp when a numbered image already exists.

In-app browser automation was unavailable in this session; the managed desktop browser connection also could not open a session. Existing installed Playwright/Chrome provided the separate browser session used for the evidence. No Windows authentication dialog was automated.

## Remaining work

The payment view now supplies an exact, source-grounded approval-policy excerpt. Charts, exports, browser uploads and natural-language operation routing remain unimplemented. The extended runner now checks payment-version compatibility and exercises four payment cases. See [payment verification](payment-policy.md) and the [release checklist](roadmap.md).
