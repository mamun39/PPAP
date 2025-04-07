# Privacy-Preserving AI Proxy (PPAP)

## Overview
PPAP is a secure AI proxy that allows users to interact with LLMs while ensuring their private data remains protected. It sanitizes user queries before forwarding them to an LLM and applies response filtering to prevent sensitive data leakage.

## Features
- **Privacy-focused query sanitization** (PII removal & redaction using pattern-based and LLM-based approaches)
- **Response filtering** to prevent sensitive data exposure
- **Secure API with authentication & rate limiting**
- **Encryption for user queries** (E2EE support in future versions)
- **Modular architecture** for local LLM integration

## Tech Stack
- **Backend:** FastAPI, Python
- **Privacy Tools:** spaCy, Presidio, PyCryptodome
- **LLM Support:** OpenAI API, Local models (Mistral, TinyLlama, Ollama)

## Installation
### Manual Setup
```sh
git clone git@github.com:mamun39/PPAP.git
cd PPAP
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
poetry install
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Project Directory Structure

```
PPAP/
│-- app/
│   │-- services/
│   │   │-- __init__.py
│   │   │-- pattern_redactor.py
│   │   │-- llm_redactor.py
│   │   │-- redactor_base.py
│   │-- utils/
│   │   │-- pii_recognizers.yaml
│   │-- __init__.py
│   │-- config.py
│   │-- main.py
│-- scripts/
│   │-- run_fastapi.sh
│   │-- test_api.sh
│-- tests/
│   │-- test_pattern_redactor.py
│   │-- test_llm_redactor.py
│-- .gitignore
│-- LICENSE
│-- POETRY.TOML
│-- README.md
```

## API Usage
After running the server, visit http://localhost:8000/docs for interactive API documentation.

### Running with Different Redactors
- Use pattern for pattern-based redaction (using PatternRedactor).
- Use llm for LLM-based redaction (using LlmRedactor with Ollama).

Example usage:

- Pattern Redactor:

```bash
./scripts/run_fastapi.sh -r pattern
```
- LLM Redactor:

```bash
./scripts/run_fastapi.sh -r llm -m llama3.2:3b
```

## Security Considerations
- Uses Zero-Trust request sanitization to filter sensitive data.
- Future updates will include end-to-end encryption for queries.
- TLS 1.3 is required for secure production deployment.

## Roadmap
- [ ] Add Web UI
- [ ] Support on-prem LLMs
- [ ] Implement Homomorphic Encryption for data privacy
- [ ] Improve PII recognition with fine-tuned NER models

## Current Limitations
- The presidio_analyzer based pattern redactor redacts PII entities (e.g., location, name, phone) irrespective of context. For example, it redacts "New York" from the sentence "What's the weather in New York?"

## Contribution
Contributions are welcome! Feel free to open an issue or submit a pull request.

## License
BUSINESS SOURCE LICENSE 1.1 © 2025 Mamunur Akand