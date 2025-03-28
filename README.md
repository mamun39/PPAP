# Privacy-Preserving AI Proxy (PPAP)

## Overview
PPAP is a secure AI proxy that allows users to interact with LLMs while ensuring their private data remains protected. It sanitizes user queries before forwarding them to an LLM and applies response filtering to prevent sensitive data leakage.

## Features
- **Privacy-focused query sanitization** (PII removal & redaction)
- **Response filtering** to prevent sensitive data exposure
- **Secure API with authentication & rate limiting**
- **Encryption for user queries** (E2EE support in future versions)
- **Modular architecture** for local LLM integration

## Tech Stack
- **Backend:** FastAPI, Python
- **Privacy Tools:** spaCy, Presidio, PyCryptodome
- **LLM Support:** OpenAI API, Local models (Mistral, TinyLlama)
- **Deployment:** Docker, Kubernetes (future)

## Installation
### Using Docker
```sh
git clone git@github.com:mamun39/PPAP.git
cd PPAP
docker build -t ppap .
docker run -p 8000:8000 ppap
```

### Manual Setup
```sh
git clone git@github.com:mamun39/PPAP.git
cd PPAP
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

## API Usage
After running the server, visit `http://localhost:8000/docs` for interactive API documentation.

## Security Considerations
- Uses **Zero-Trust request sanitization** to filter sensitive data.
- Future updates will include **end-to-end encryption for queries**.
- TLS 1.3 is required for secure production deployment.

## Roadmap
- [ ] Add Web UI
- [ ] Support on-prem LLMs
- [ ] Implement Homomorphic Encryption for data privacy
- [ ] Improve PII recognition with fine-tuned NER models

## Contribution
Contributions are welcome! Feel free to open an issue or submit a pull request.

## License
MIT License © 2025 Your Name / Company

