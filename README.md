# Secure File Encryption & Sharing System

## Abstract
This project implements a robust secure file sharing system leveraging hybrid cryptographic techniques. It combines the efficiency of symmetric encryption (AES-256-GCM) for large files with the security of asymmetric encryption (RSA-OAEP) for key wrapping, and RSA-PSS for digital signatures. Built with Flask, MySQL, and Bootstrap 5, it serves as a practical implementation of applied cryptography principles for a university project.

## Problem Statement
In an era of increasing digital communication, unencrypted file sharing exposes sensitive data to unauthorized access, interception, and tampering. Many existing solutions either lack strong end-to-end security guarantees or are too complex for average users, creating a need for a secure, educational, and accessible file-sharing platform.

## Objectives
1. Implement secure file encryption using AES-256-GCM.
2. Enable secure key exchange using RSA-OAEP.
3. Provide non-repudiation and integrity via RSA-PSS digital signatures.
4. Develop a secure user authentication system using Argon2id.
5. Create a robust sharing mechanism with granular access controls (revocation, expiration).
6. Implement comprehensive audit logging for all critical actions.
7. Protect against common web vulnerabilities (OWASP Top 10).
8. Build an intuitive user interface using Bootstrap 5.

## Features
### Core Features
- File Upload & Download
- Granular File Sharing (with expiration and revocation)
- User Dashboard & File Management
### Security Features
- Hybrid Encryption (AES + RSA)
- Digital Signatures
- Integrity Verification
- Rate Limiting & CSRF Protection
- Comprehensive Audit Logs
### Educational Features
- Real-time cryptographic explanations
- Transparent security controls view

## Architecture

```mermaid
graph TB
    Client[Web Browser] -->|HTTPS| Flask[Flask Application]
    Flask --> Auth[Auth Service]
    Flask --> Crypto[Crypto Service]
    Flask --> FileSystem[Local File Storage]
    Flask --> DB[(MySQL Database)]
    
    Crypto -.-> AES[AES-256-GCM]
    Crypto -.-> RSA[RSA-OAEP / RSA-PSS]
```

## Technology Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | HTML5/CSS3, Bootstrap 5 | User Interface |
| Backend | Python 3.12+, Flask | Web Framework |
| Database | MySQL 8.0+ | Relational Data Storage |
| Cryptography | `cryptography` Python package | Secure primitives |

## Cryptographic Algorithms
| Algorithm | Standard | Purpose | Key Size |
|-----------|----------|---------|----------|
| AES-GCM | FIPS 197, NIST SP 800-38D | File Encryption (Symmetric) | 256-bit |
| RSA-OAEP | PKCS#1 v2.2, RFC 8017 | Key Wrapping (Asymmetric) | 2048-bit |
| RSA-PSS | PKCS#1 v2.2, RFC 8017 | Digital Signatures | 2048-bit |
| SHA-256 | FIPS 180-4 | Integrity Hashing | 256-bit |
| Argon2id | RFC 9106 | Password Hashing | N/A |

## Hybrid Encryption Flow

```mermaid
graph LR
    subgraph Encryption
        Plaintext --> AES[AES-256-GCM]
        AESKey[Unique AES Key] --> AES
        AES --> Ciphertext
        AESKey --> RSA[RSA-OAEP]
        RecipientPubKey[Recipient Public Key] --> RSA
        RSA --> EncryptedAESKey
    end
    subgraph Signing
        Hash[SHA-256 File Hash] --> RSAPSS[RSA-PSS]
        SenderPrivKey[Sender Private Key] --> RSAPSS
        RSAPSS --> Signature
    end
```

## Database Design

```mermaid
erDiagram
    USERS ||--o{ FILES : "owns"
    USERS ||--o{ FILE_KEYS : "has"
    USERS ||--o{ FILE_SHARES : "receives"
    USERS ||--o{ AUDIT_LOGS : "generates"
    USERS ||--o{ LOGIN_ATTEMPTS : "makes"
    FILES ||--o{ FILE_KEYS : "encrypted with"
    FILES ||--o{ FILE_SHARES : "shared via"
```

### Table Overview
- `users`: Stores user credentials and RSA public keys.
- `files`: Stores encrypted file metadata and signatures.
- `file_keys`: Stores the wrapped AES keys for each recipient.
- `file_shares`: Manages access permissions, expirations, and revocations.
- `audit_logs`: Records system events.
- `login_attempts`: Tracks failed logins for rate limiting.

## API Endpoints
| Method | URL | Auth Required | Description |
|--------|-----|---------------|-------------|
| POST | `/auth/login` | No | Authenticate user |
| POST | `/auth/register` | No | Register new user |
| GET | `/auth/logout` | Yes | Terminate session |
| POST | `/files/upload` | Yes | Upload and encrypt file |
| GET | `/files/list` | Yes | List owned files |
| GET | `/files/<id>` | Yes | View file details |
| GET | `/files/download/<id>` | Yes | Decrypt and download |
| POST | `/files/delete/<id>` | Yes | Delete file |
| POST | `/sharing/share` | Yes | Share file with user |
| GET | `/sharing/shared-with-me` | Yes | View received files |
| POST | `/sharing/revoke/<id>` | Yes | Revoke share access |
| GET | `/profile` | Yes | User settings |
| GET | `/admin` | Yes (Admin) | System oversight |

## Installation

### Prerequisites
- Python 3.12+
- MySQL 8+
- Git

### Quick Start
1. Clone repo: `git clone <url>`
2. Create venv: `python -m venv venv` and activate it.
3. Install requirements: `pip install -r requirements.txt`
4. Create MySQL database: `CREATE DATABASE secure_file_sharing;`
5. Copy `.env.example` to `.env` and configure credentials.
6. Initialize database: `python scripts/init_db.py`
7. Create admin: `python scripts/create_admin.py`
8. Run server: `python run.py`
9. Access at `http://localhost:5000`

### Docker Setup
Run `docker-compose up --build` to start the application with an integrated MySQL database.

## Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| FLASK_APP | Entry point | `run.py` |
| SECRET_KEY | Flask secret key | (Must be set) |
| DATABASE_URI | MySQL connection string | `mysql+pymysql://user:pass@localhost/db` |
| UPLOAD_FOLDER | Directory for encrypted files | `./uploads` |

## Running Tests
Run the test suite using pytest:
`pytest tests/ -v`

## Demo Scenario
1. **Alice** registers and logs in.
2. Alice generates an RSA key pair automatically during registration.
3. **Bob** registers and logs in.
4. Alice uploads `secret.txt`. The system generates a unique AES key, encrypts the file, and wraps the AES key with Alice's public key.
5. Alice signs the file hash with her private key.
6. Alice shares `secret.txt` with Bob.
7. The system decrypts the AES key using Alice's private key (temporarily derived from her session) and re-wraps it with Bob's public key.
8. Bob logs in and navigates to "Shared with me".
9. Bob downloads the file. The system unwraps the AES key using his private key and decrypts the file.
10. The system verifies Alice's signature to ensure authenticity.

## Security Considerations
- Argon2id for password hashing.
- AES-256-GCM provides authenticated encryption.
- RSA-OAEP prevents chosen-ciphertext attacks on key wrapping.
- Rate limiting on login endpoints.
- CSRF protection on all forms.
- Secure session cookies (HttpOnly, Secure flags in production).

## Limitations
1. Server-side decryption requires trust in the server.
2. Lack of client-side encryption.
3. No Multi-Factor Authentication (MFA).
4. No automated key rotation.
5. Absence of Hardware Security Module (HSM) integration.
6. Derived private keys are temporarily stored in memory/session.
7. No real-time sharing notifications.
8. Limited testing scope (university project context).

## Future Improvements
- Implement Client-Side Encryption (WebCrypto API).
- Integrate Elliptic Curve Cryptography (ECC) for smaller keys.
- Add MFA support.
- Cloud storage integration (AWS S3).
- Implement hardware-backed key storage (KMS).

## Project Structure
```text
secure_file_sharing/
├── app/
│   ├── auth/
│   ├── core/
│   ├── files/
│   ├── models/
│   ├── templates/
│   └── utils/
├── tests/
├── scripts/
├── docs/
├── uploads/
├── requirements.txt
├── run.py
└── README.md
```

## Screenshots
*(Add screenshots of Login, Dashboard, and Sharing views here)*

## Authors
Student Name - University Project

## License
MIT License
