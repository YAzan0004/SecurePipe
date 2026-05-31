# SecurePipe

<p align="center">
  <strong>Privacy-Aware AI Middleware for Protecting Sensitive Data Before AI Processing</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-green" />
  <img src="https://img.shields.io/badge/SQLite-Database-lightgrey" />
  <img src="https://img.shields.io/badge/AI-OpenAI%20API-purple" />
  <img src="https://img.shields.io/badge/Project-Graduation%20Project-orange" />
</p>

---

## 📌 Project Overview

**SecurePipe** is a privacy-aware AI middleware system designed to protect sensitive user information before sending requests to an AI model.

The system works as a secure gateway between the user and the AI provider. It receives user input, detects sensitive information, masks confidential values, and forwards only the sanitized version to the AI model.

This helps reduce the risk of exposing private information when using AI-powered applications.

---

## 🎓 Course

**Graduation Project**

---

## 👨‍🏫 Supervisor

**Dr. Ismail Keshta**

---

## 👥 Team Members

| Name | Student ID | Role |
|---|---:|---|
| Yazan Alanazi | 221120003 | Project Leader |
| Hamiza Matter | 221120320 | Team Member |
| Saad Alarifi | 221129287 | Team Member |

---

## 🤝 Team Contribution

SecurePipe was completed through collaborative teamwork.

All team members participated in the main project stages, including planning, development, testing, documentation, and final preparation.

As the project leader, **Yazan Alanazi** was responsible for coordinating the project work, organizing development tasks, following up on implementation progress, and preparing the final source code submission.

The final outcome represents the shared effort of the team across system design, backend development, sanitization logic, AI integration, user interface development, testing, and documentation.

---

## ❗ Problem Statement

AI applications often send user input directly to external AI providers. This may create privacy risks when the input contains sensitive or confidential information.

Users may accidentally include data such as:

- Email addresses
- Phone numbers
- National ID numbers
- Iqama numbers
- Passport numbers
- Passwords
- OTP codes
- Bank card numbers
- IBAN numbers
- IP addresses

SecurePipe addresses this problem by detecting and masking sensitive data before the request reaches the AI model.

---

## 🎯 Project Objectives

The main objectives of SecurePipe are:

- Detect sensitive information from user input.
- Mask confidential data before AI processing.
- Support direct text processing.
- Support uploaded files such as PDF, TXT, and DOCX.
- Send only sanitized content to the AI provider.
- Keep the AI model separate from the privacy protection layer.
- Generate logs and evidence records for testing and validation.
- Provide a simple web-based chat interface.
- Provide an admin dashboard for monitoring.

---

## ⚙️ How SecurePipe Works

SecurePipe follows a simple privacy-focused processing flow:

```text
User Input
   ↓
SecurePipe Middleware
   ↓
Sensitive Data Detection
   ↓
Data Masking / Sanitization
   ↓
Sanitized Request
   ↓
AI Provider
   ↓
AI Response
   ↓
User Interface
```

When the user submits a message or uploads a file, SecurePipe checks the content before sending it to the AI model.

Detected sensitive values are replaced with safe placeholders such as:

- `[EMAIL]`
- `[PHONE]`
- `[NATIONAL_ID]`
- `[IBAN]`
- `[PASSPORT]`
- `[CARD_PAN]`
- `[IP_ADDRESS]`
- `[MAC_ADDRESS]`

The AI model receives only the sanitized version of the request.

---

## 🔐 Supported Sensitive Data Types

SecurePipe can detect and mask multiple types of sensitive data, including:

| Sensitive Data Type | Placeholder |
|---|---|
| Email Address | `[EMAIL]` |
| Phone Number | `[PHONE]` |
| National ID | `[NATIONAL_ID]` |
| Iqama Number | `[NATIONAL_ID]` |
| Passport Number | `[PASSPORT]` |
| IBAN | `[IBAN]` |
| Bank Card Number | `[CARD_PAN]` |
| IP Address | `[IP_ADDRESS]` |
| MAC Address | `[MAC_ADDRESS]` |
| User Identifier | `[USER_ID]` |
| OTP / Password-like Values | Masked Placeholder |

---

## ✨ Key Features

- Rule-based sensitive data detection.
- Automatic masking before AI processing.
- Direct text input processing.
- File upload processing.
- PDF text extraction.
- TXT file processing.
- DOCX file processing.
- OpenAI API integration.
- Web-based chat interface.
- Conversation management.
- Admin dashboard.
- Request logging.
- Evidence generation during local testing.
- Request ID tracking for traceability.
- Modular structure for future extension.

---

## ✅ Benefits of the System

SecurePipe provides several practical benefits:

- Reduces the risk of sending sensitive data to AI providers.
- Supports safer interaction with AI tools.
- Applies privacy-by-design principles.
- Keeps the AI model separate from the security layer.
- Makes the system easier to maintain and extend.
- Supports future integration with different AI providers.
- Demonstrates how middleware can improve privacy in AI-driven applications.

---

## 🧰 Technologies Used

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
| HTML | Web page structure |
| CSS | Interface styling |
| JavaScript | Frontend interaction |
| PowerShell | Local development commands |
| GitHub | Source code hosting and version control |

---

## 📁 Project Structure

```text
SecurePipe/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── schemas.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── process.py
│   │       ├── sanitize.py
│   │       ├── admin.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── sanitizers.py
│   │   ├── ai_client.py
│   │   ├── database.py
│   │   ├── evidence.py
│   │   ├── file_extractor.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   └── security.py
│   │
│   └── web/
│       ├── index.html
│       └── admin.html
│
├── evidence/
├── logs/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧩 Main Components

### 1. User Interface

The web interface allows users to enter messages, upload files, and receive AI responses through a simple chat-based design.

### 2. API Layer

The backend API receives user requests, validates input, manages uploaded files, and passes content to the processing pipeline.

### 3. Sanitization Engine

The sanitization engine detects sensitive information using predefined rule-based patterns and replaces detected values with safe placeholders.

### 4. AI Client

The AI client sends the sanitized request to the configured AI provider and returns the generated response to the user.

### 5. Logging and Evidence

The system records request activity, detected sensitive data types, sanitized outputs, and evidence files to support testing and validation.

### 6. Admin Dashboard

The admin dashboard provides basic monitoring capabilities for reviewing system activity during testing and demonstration.

---

## 🧾 Testing and Validation

The system was tested locally using different types of sensitive data and file formats.

Testing focused on:

- Detecting sensitive data in direct text input.
- Detecting sensitive data inside uploaded files.
- Masking detected values correctly.
- Sending only sanitized content to the AI provider.
- Generating logs and evidence records.
- Verifying the web interface.
- Verifying the admin dashboard.
- Checking system behavior using different sample inputs.

---

## ⚠️ Limitations

SecurePipe is a prototype developed for graduation project purposes.

Current limitations include:

- Detection is mainly based on predefined rule-based patterns.
- The system may not detect all possible sensitive data formats.
- Some complex document structures may affect file text extraction.
- The system was tested in a local development environment.
- The admin dashboard provides basic monitoring features only.
- The project is not intended as a production-ready enterprise security system.


---


## 📄 Disclaimer

SecurePipe was developed as an academic graduation project.

It demonstrates the concept of privacy-aware middleware for AI systems. The system is intended for learning, testing, and demonstration purposes only.
