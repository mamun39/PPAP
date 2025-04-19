# Privacy-Preserving AI Proxy (PPAP)

[![License](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](https://github.com/mamun39/PPAP)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-%2300ac47)](https://fastapi.tiangolo.com)


PPAP is a secure AI proxy designed to protect user privacy when interacting with Large Language Models (LLMs). It sanitizes user queries before forwarding them to an LLM and (in future releases) will filter LLM responses to further limit the risk of sensitive data exposure.

---

## Table of Contents
1. [Features](#features)  
2. [Tech Stack](#tech-stack)  
3. [Installation](#installation)  
4. [Project Structure](#project-structure)  
5. [Usage](#usage)  
    - [API Documentation](#api-documentation)  
    - [Running with Different Redactors](#running-with-different-redactors)  
6. [Security Considerations](#security-considerations)  
7. [Roadmap](#roadmap)  
8. [Current Limitations](#current-limitations)  
9. [Contribution](#contribution)  
10. [License](#license)  

---

## Features

- **Privacy-Focused Query Sanitization**  
  Removes or redacts personally identifiable information (PII) through both pattern-based (regex, rules) and LLM-based (contextual analysis) approaches.  
- **Modular LLM Integration**  
  Can be extended to use local or remote LLMs (e.g., OpenAI, Mistral, TinyLlama, Ollama).  
- **Upcoming Features**  
  - Response filtering to prevent sensitive data leakage  
  - Secure API endpoints with authentication & rate limiting  
  - End-to-end encryption (E2EE) for user queries  

---

## Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), Python  
- **Privacy Tools:** [spaCy](https://spacy.io/), [Microsoft Presidio](https://microsoft.github.io/presidio/), [PyCryptodome](https://github.com/Legrandin/pycryptodome)  
- **LLM Support:** [OpenAI API](https://platform.openai.com/docs/introduction), Local models (Mistral, TinyLlama, [Ollama](https://github.com/jmorganca/ollama))  

---

## Installation

PPAP can be installed and run manually. In future versions, containerized deployment (e.g., Docker) will also be supported.

### Manual Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:mamun39/PPAP.git
   cd PPAP
   ```
2. Create and activate a virtual environment:  
   - On macOS/Linux:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```
   - On Windows:
     ```powershell
     python -m venv venv
     venv\Scripts\activate
     ```
3. Install dependencies (using Poetry):
   ```bash
   poetry install
   ```
4. Run the FastAPI application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

## Project Structure

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

- The `app` directory contains the main application code.  
- The `services` folder encapsulates logical components for redaction.  
- The `utils` folder stores additional configuration files or assets (e.g., `pii_recognizers.yaml`).  
- `scripts` contains helper scripts for running or testing the application.  
- `tests` contains unit tests related to each redactor.

---

## Usage

### API Documentation

Once the FastAPI server is running, open your browser at:
[http://localhost:8000/docs](http://localhost:8000/docs)

This Swagger-based interactive documentation allows you to explore and test the API endpoints.

### Running with Different Redactors

Depending on your requirements, you can choose between:
- **Pattern-Based Redaction** using rule-based PII detection (PatternRedactor).  
- **LLM-Based Redaction** using contextual analysis powered by local or remote LLMs (LlmRedactor).  

Example Scripts:
- Pattern Redactor:
  ```bash
  ./scripts/run_fastapi.sh -r pattern
  ```
- LLM Redactor (e.g., specifying a particular model):
  ```bash
  ./scripts/run_fastapi.sh -r llm -m llama3.2:3b
  ```

---

## Security Considerations

- **Zero-Trust Sanitization**: Queries undergo thorough filtering to minimize sensitive data exposure before being processed by an LLM.  
- **Priority on Encryption**: Future releases will include end-to-end encryption (E2EE) for secure data transmission.  
- **TLS Requirement**: For production deployments, ensure at least TLS 1.3 is enabled to protect data in transit.

---

## Roadmap

- [x] Support on-prem/local LLM usage  
- [ ] Add a web-based UI for interactive usage  
- [ ] Implement Homomorphic Encryption for advanced data privacy  
- [ ] Enhance PII recognition via fine-tuned NER models  

---

## Current Limitations

- **Context-Agnostic Redaction**: The default Presidio analyzer redacts identified PII (e.g., location, names, phone numbers) without context. For instance, "New York" is redacted even if it’s a non-sensitive mention like “What’s the weather in New York?”

---

## Contribution

Contributions are welcome!  
- Feel free to open an issue for bugs or feature requests.  
- Submit pull requests following our coding guidelines (coming soon in CONTRIBUTING.md).  

---

## License

Distributed under the MIT License © 2025 Mamunur Akand.  
See [LICENSE](./LICENSE) for more information.
