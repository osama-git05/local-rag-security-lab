# Remaining work and release checklist

Updated 5 November 2026. The [final report](final-report.md) summarizes completed work. The [implementation log](implementation-log.md) preserves the earlier checkpoints.

## Verified development milestones

- [x] Verify server-assigned roles and employee/admin retrieval on the existing Chroma index.
- [x] Exercise the known onboarding injection, administrator-role claims and prompt-extraction request.
- [x] Validate citation IDs and retest the two previously rejected safe refusal messages.
- [x] Build the administrator payment view, versioned fixture and policy provenance.
- [x] Capture environment snapshots and pass 126 isolated checks, three index checks and 16 live cases.
- [x] Verify browser payment flows, employee login, chat loading and safe retry.
- [x] Verify locked dependency installation and payment smoke checks in a clean copy of the current source.
- [x] Record model and weight identity, observed local recipe and conflicting publisher terms.
- [x] Prepare the file list, review evidence and write the project report and demo walkthrough.

## Before a reproducible release

- [x] Commit the reviewed source, demo and selected evidence.
- [x] Verify a fresh checkout with a pinned install, new index and 16 live cases using the installed Ollama models. [Checkout report](../results/fresh-checkout-verification-20261105T113532797194Z.json).
- [x] Verify the local model reconstruction against the exact installed manifest digest. [Rebuild record](../results/model-local-rebuild-verified-20261105T112908555213Z.json).
- [ ] Resolve terms for redistribution of the exact merged model or validate a separately licensed replacement.
- [x] Rotate the active credential pair and verify both old values are rejected by the running API. [Rotation evidence](../results/credential-rotation-20261105T112710208082Z.json).
- [x] Record the demo and retain reviewed captures for its visible milestones. [Demo video](exampleco-portfolio-demo.mp4) · [Demo walkthrough](demo.md).

## Further evaluation and features

- [ ] Add a held-out attack set, factual-support grading and controlled comparisons with fixed model, corpus and settings.
- [ ] Add credential-independent CI and expand authorization coverage for any future read paths.
- [ ] Evaluate natural-language payment routing, charts, exports and uploads as separate product work.

The current results use known development cases. The evidence records specific behavior under the captured environment. [Test results](testing.md) · [Evidence index](evidence.md).
