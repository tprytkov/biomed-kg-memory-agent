# Model Card

## Default Mode

The default extractor is rule based. It uses a small biomedical lexicon and relation trigger phrases to extract typed entities and temporal relations from synthetic notes.

## Optional Local Hugging Face Mode

When `EXTRACTION_MODE=hf_local`, the project loads a local SentenceTransformer model and uses embedding similarity to rerank relation confidence. This is local-only and does not call OpenAI.

## Limitations

- The synthetic corpus is small and designed for demonstration, not clinical use.
- Rule extraction is transparent but brittle outside the included biomedical phrasing.
- The project should not be used for medical decision-making.
