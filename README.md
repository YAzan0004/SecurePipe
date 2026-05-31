# SecurePipe

**SecurePipe** is a privacy-aware AI middleware system designed to protect sensitive user information before sending requests to an AI model.

The system detects confidential data from user input, masks it, and forwards only the sanitized version to the AI provider.

---

## Course

**Graduation Project**

---

## Supervisor

**Dr. Ismail Keshta**

---

## Team Members

| Name | Student ID | Role |
|---|---:|---|
| Yazan Alanzi | 221120003 | Project Leader |
| Hamiza Matter | 221120320 | Team Member |
| Saad Alarifi | 221129287 | Team Member |

---

## Team Contribution

The project was completed through collaborative teamwork. All team members participated in planning, development, testing, and documentation.

As the project leader, **Yazan Alanzi** was responsible for coordinating the project work, organizing development tasks, following up on implementation progress, and preparing the final source code submission.

The final outcome represents the shared effort of the team across the main stages of the project, including system design, backend development, sanitization logic, AI integration, user interface development, testing, and documentation.

---

## Project Description

SecurePipe is a web-based middleware system designed to improve privacy and security when users interact with AI systems.

The main idea is to place a secure layer between the user and the AI model. Before any request reaches the AI provider, SecurePipe checks the input and masks sensitive information.

The system performs the following:

- Receives user text or uploaded file content.
- Detects sensitive information inside the input.
- Masks sensitive data before AI processing.
- Sends only the sanitized text to the AI provider.
- Returns the AI response to the user.
- Stores logs and evidence records for testing and validation.

SecurePipe helps reduce the risk of exposing private information such as emails, phone numbers, national IDs, iqama numbers, passports, passwords, OTP codes, card numbers, IBANs, IP addresses, and other sensitive data.

---

## Key Features

- Sensitive data detection using rule-based patterns.
- Data masking before sending requests to the AI model.
- Direct text processing.
- File upload processing for PDF, TXT, and DOCX files.
- OpenAI API integration using a ChatGPT model.
- Web-based chat interface.
- Conversation management.
- Admin dashboard for monitoring.
- Request logging.
- Evidence generation during local testing.
- Request ID tracking for traceability.

---

## Benefits of the System

- Reduces the risk of sending sensitive data to AI services.
- Supports safer interaction with AI tools.
- Applies privacy-by-design principles.
- Keeps the AI model separate from the security layer.
- Makes the system easier to extend with other AI providers.
- Demonstrates how middleware can improve privacy in AI-driven applications.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| FastAPI | Backend API framework |
| Uvicorn | ASGI server for running the application |
| SQLite | Local database |
| SQLAlchemy | Database models and ORM |
| Pydantic | Request and response validation |
| OpenAI API | AI provider integration |
| Regex | Sensitive data detection and masking |
| pdfplumber | PDF text extraction |
| python-docx | DOCX text extraction |
| python-multipart | File upload handling |
| HTML, CSS, JavaScript | Web interface |
| PowerShell | Local development commands |
| GitHub | Source code hosting and version control |

---

## Project Structure

```text
SecurePipe/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── schemas.py
│   │   └── routes/
│   ├── core/
│   │   ├── sanitizers.py
│   │   ├── ai_client.py
│   │   ├── database.py
│   │   ├── evidence.py
│   │   ├── file_extractor.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   └── security.py
│   └── web/
│       ├── index.html
│       └── admin.html
│
├── requirements.txt
├── .env.example
├── .gitignore
└── SecurePipe_README.docx
