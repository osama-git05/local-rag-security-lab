# ExampleCo demo walkthrough

The **61-second captioned demo** uses live browser sessions for the employee and administrator flows and closes with a summary of the saved regression results. Sign-in took place before capturing each role. The recording uses on-screen captions and has no audio track. [Watch the MP4](exampleco-portfolio-demo.mp4) · [Capture record](../results/demo-capture-20261105T111802199000Z.json).

| Time | Scene |
| --- | --- |
| 0:04 | Employee leave question and permitted sources |
| 0:20 | Employee finance refusal |
| 0:35 | Employee payment boundary |
| 0:39 | Administrator October result with policy and dataset details |
| 0:48 | Administrator November result |
| 0:54 | Saved regression results |

## Four-minute live walkthrough

Show a normal employee answer, the finance access boundary, an exact administrator payment result and the evidence behind those behaviors. [Project report](final-report.md).

## Prepare the workspace

1. Open the [local assistant](http://127.0.0.1:8001/) and confirm the company page loads. If the server is down, use the existing setup instructions. Verify that Ollama and the current index are available. [Setup](setup.md).
2. Confirm the synthetic payment fixture is active. October 2026 should show three rows and 18,750.125 BHD as administrator. Preserve an existing activation when it already matches the fixture.
3. Open the saved 16-case report and evidence index in separate tabs. Keep the [administrator result](screenshots/68-payments-with-policy-provenance.png), [employee boundary](screenshots/69-employee-policy-boundary.png) and [employee answer](screenshots/73-chat-live-recovery.png) ready as labelled recorded evidence if a live step is slow.
4. Pause recording while connecting or changing accounts. Resume after the token dialog closes and the verified role is visible. Frame the browser content and keep unrelated windows and notifications outside the capture.

## Recording sequence

| Time | Action | Narration and visible proof |
| --- | --- | --- |
| 0:00–0:25 | Open the company assistant with the employee role visible | “ExampleCo is a local assistant for a fictional company. This session is verified as an employee.” |
| 0:25–1:05 | Ask **How much annual leave do employees receive?** with Enter | Let the loading state appear. “The assistant returns 25 days and shows the leave policy among its permitted sources.” Point to the source panel. |
| 1:05–1:45 | Ask **When does the finance team review supplier payments, and what approval is needed above 5,000 BHD?** Then scroll to Supplier payments | “The employee has no finance answer or administrator source. The payment controls are also restricted.” If the live model returns a safe error, describe the observed outcome and use the retained employee evidence to show the expected refusal. |
| 1:45–2:55 | Reconnect as administrator off camera. Select October 2026 and click **View payments** | “October has three payments above 5,000 BHD, totaling 18,750.125 BHD. The system computes that total directly from the dataset.” Show the row source lines. Expand **Dataset & calculation details** and **Policy source details**. “The policy calls for Friday reviews and two administrators’ approval above the threshold. The payment records do not establish approval status.” |
| 2:55–3:20 | Select November 2026 and click **View payments** | “November has one qualifying payment for 8,000.000 BHD. The result and its sources stay tied to the selected month and the active dataset.” |
| 3:20–4:00 | Open the current case report | “The saved run passed 126 isolated checks, three index checks and 16 live cases. These fixtures exercise specific access, output and payment behaviors.” Show the four payment cases and the employee 403. Close with the report link. |

[Current case report](../results/development-regression-20261105T103930390851Z.json) · [Screenshot index](evidence.md).

The 5 November live API preflight confirmed both scripted employee prompts, employee payment denial and the October and November administrator totals.

## Capture plan

The recorded demo produced screenshots **74–76** of the employee answer, employee payment boundary, and administrator result with expanded provenance. The closing card is based on the saved workflow evidence. [Screenshot index](evidence.md).
