# Local model provenance

## Generation model

The 5 November 2026 Ollama inspection identified `optimized-gemma:latest` as a Gemma 4 model with 4.6 billion parameters and Q4_K_M quantization. Its local manifest digest is `sha256:c40843ebaf9db6190dc77cfcb5049a7508a56cd9c14eae7eff12e35129872e92`, shared with the local alias `scam-bot:latest`.

Its weight layer `sha256:c113003e49b792dd9974d8dc21c16d569ce4cc7673a9a10a68ddaa998b03ed16` exactly matches the locally installed `alicek0914/gemma4-scam:latest`. The published tag shows the same short manifest digest `73160c907d9f` as that local source tag. The publisher describes a merged QLoRA fine-tune of the Unsloth Gemma 4 E2B instruction model. The local optimized tag and published source have different parameter layers. [Publisher’s Ollama model card](https://ollama.com/alicek0914/gemma4-scam:latest).

### Observed local recipe

The installed manifest contains a weight layer and a parameter layer. `ollama show optimized-gemma:latest --modelfile` points to the local Ollama blob and reports these directives:

```text
TEMPLATE {{ .Prompt }}
PARAMETER repeat_penalty 1.2
PARAMETER stop <turn|>
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 1024
PARAMETER num_gpu 99
PARAMETER num_predict -1
```

The app supplies temperature 0, context 4096 and a 256-token output limit at request time. The directives above record the installed defaults. Rebuilding the exported Modelfile from the local blob reproduced the weight and template but yielded a different parameter layer and manifest. [Modelfile attempt](../results/model-local-rebuild-20261105T112755792289Z.json) · [Ollama Modelfile reference](https://docs.ollama.com/modelfile).

An exact rebuild succeeded using Ollama’s local `POST /api/create` API with `from` set to the verified installed publisher tag `alicek0914/gemma4-scam:latest` and the full parameter object below. Use a distinct local verification tag for `model` and set `stream` to false. The rebuild matched the original manifest byte for byte, including its weight and parameter layers, and the temporary tag was removed. [Verified rebuild](../results/model-local-rebuild-verified-20261105T112908555213Z.json).

```json
{
  "num_ctx": 1024,
  "num_gpu": 99,
  "num_predict": -1,
  "repeat_penalty": 1.2,
  "stop": ["<turn|>"],
  "temperature": 0.3,
  "top_p": 0.9
}
```

### License evidence

Google lists Apache 2.0 for the Gemma 4 base family. The publisher’s Ollama listing states research and non-commercial terms for the merged weights and adapter, while its separate Hugging Face adapter card displays Apache 2.0. The installed merged artifact contains no embedded license text. The applicable terms for redistribution of that specific merged artifact remain unresolved. A distributable release needs clarification from the publisher for that artifact or a separately licensed replacement with its own regression evidence. [Google Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4), [Ollama publisher license section](https://ollama.com/alicek0914/gemma4-scam:latest#license), [Hugging Face adapter card](https://huggingface.co/Alice0914/gemma4-e2b-scam-sentinel).

The release candidate contains application source and synthetic evidence. Keep both model artifacts external to the source package. The verified rebuild used already-installed model data.

## Embedding model

The installed `embeddinggemma:latest` manifest digest is `sha256:85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`. Its metadata identifies the Gemma 3 architecture and a `gemma` license label. The embedded Gemma Terms of Use are dated 24 March 2025. Google lists the original EmbeddingGemma in the Gemma Terms appendix. Record the applicable terms and exact model revision when preparing a separate installation. [EmbeddingGemma model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card), [Google Gemma Terms](https://ai.google.dev/gemma/terms/).
