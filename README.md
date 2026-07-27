# ⛓ CertChain — Cloud-Native Certificate Verification System

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-6.0-green?style=flat-square&logo=django)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?style=flat-square&logo=amazonaws)
![Ethereum](https://img.shields.io/badge/Ethereum-Blockchain-3C3C3D?style=flat-square&logo=ethereum)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?style=flat-square&logo=postgresql)

> A tamper-proof digital certificate verification system secured by SHA-256 cryptographic hashing and Ethereum blockchain anchoring. Built with Django, PostgreSQL, Docker, Nginx, and deployed on AWS EC2.

---

## 🌐 Live Demo

```
http://13.204.65.237
```

| Role | URL | Credentials |
|------|-----|-------------|
| Public Verify | `/verify/` | No login required |
| Staff Dashboard | `/dashboard/` | sarah.johnson / Staff@1234 |
| Django Admin | `/admin/` | root / (admin password) |

---

## 🎯 What Problem Does This Solve?

Certificate fraud is a global problem. Employers cannot instantly verify whether a degree or certification is genuine. Manual verification is slow, expensive, and unreliable — especially across borders.

**CertChain solves this with a dual-layer trust model:**

```
Layer 1 — Technology (CertChain handles this):
  → SHA-256 hash guarantees the certificate was not tampered with after issuance
  → Ethereum blockchain provides immutable, permanent proof of existence
  → Anyone can verify in seconds via Certificate ID

Layer 2 — Institutional Trust (Institution handles this):
  → The issuing institution verifies the student actually earned the certificate
  → This mirrors how all real credentials work (degrees, passports, licenses)
```

---

## ✨ Key Features

- 🔐 **SHA-256 Cryptographic Hashing** — every certificate gets a unique tamper-proof fingerprint
- ⛓ **Ethereum Blockchain Anchoring** — certificate hashes stored permanently on-chain via Solidity smart contract
- 📄 **PDF Upload Support** — hash generated from actual PDF content for stronger integrity
- 🌐 **REST API** — full API with JWT authentication for third-party integrations
- 👥 **Staff Dashboard** — custom portal for institution staff to issue and manage certificates
- 📧 **Automatic Email Notification** — students receive Certificate ID, SHA-256 hash, and blockchain TX hash by email
- 🐳 **Fully Containerized** — 4-service Docker Compose stack (Django, PostgreSQL, Nginx, Ganache)
- ☁️ **AWS EC2 Deployed** — live on cloud with Nginx reverse proxy and Gunicorn

---

## 🏗️ System Architecture

```
User (Browser)
      ↓
Nginx (Reverse Proxy — port 80)
      ↓
Django + Gunicorn (Application — port 8000)
      ↓
PostgreSQL (Database — port 5432)
      ↓
Ganache (Ethereum Blockchain — port 8545)
```

### Docker Services

```yaml
certchain_nginx    → Nginx reverse proxy
certchain_web      → Django + Gunicorn
certchain_db       → PostgreSQL 17
certchain_ganache  → Local Ethereum blockchain
```

---

## 🔄 Certificate Lifecycle

```
1. Staff logs into dashboard
2. Fills in student details + optional PDF upload
3. System generates SHA-256 hash from data or PDF
4. Hash stored in PostgreSQL
5. Hash anchored to Ethereum blockchain → TX hash returned
6. Student receives email with Certificate ID + Hash + TX Hash
7. Anyone can verify at /verify/ using Certificate ID
8. System confirms: DB record ✅ + Blockchain record ✅
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Django 6 + DRF | Web framework + REST API |
| Database | PostgreSQL 17 | Certificate storage |
| Cryptography | SHA-256 (hashlib) | Tamper-proof hashing |
| Blockchain | Ethereum + Web3.py | Immutable proof anchoring |
| Smart Contract | Solidity + py-solc-x | On-chain hash storage |
| Local Chain | Ganache | Ethereum development blockchain |
| Auth | JWT (simplejwt) | API authentication |
| Containerization | Docker + Compose | Multi-service orchestration |
| Web Server | Nginx + Gunicorn | Production deployment |
| Cloud | AWS EC2 (Mumbai) | Public deployment |
| Email | Gmail SMTP | Student notifications |
| PDF Processing | PyPDF2 | PDF content hashing |

---

## 🚀 Local Development Setup

### Prerequisites
```
Python 3.13+
PostgreSQL 17
Docker Desktop
Git
```

### 1. Clone the repository
```bash
git clone https://github.com/TJunior03/certchain.git
cd certchain
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
```env
SECRET_KEY=your-secret-key-here
DB_NAME=certchain_db
DB_USER=certchain_user
DB_PASSWORD=certchain1234
DB_HOST=127.0.0.1
DB_PORT=5432
DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=certchain@system.com
```

### 5. Run migrations
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run locally
```bash
python manage.py runserver
```

---

## 🐳 Docker Deployment

### Run full stack
```bash
# Change DB_HOST=db in .env first
docker compose build
docker compose up -d

# Run migrations inside container
docker exec certchain_web python manage.py migrate
docker exec certchain_web python manage.py collectstatic --noinput
docker exec -it certchain_web python manage.py createsuperuser
```

### Access
```
http://localhost        → Home page
http://localhost/dashboard/  → Staff portal
http://localhost/admin/ → Django admin
http://localhost/verify/ → Public verify
```

---

## 🌐 REST API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/token/` | None | Get JWT token |
| `POST` | `/api/token/refresh/` | None | Refresh JWT token |
| `POST` | `/api/issue/` | JWT | Issue certificate + blockchain anchor |
| `POST` | `/api/verify/` | None | Verify certificate by UUID |
| `GET` | `/api/certificates/` | JWT | List all certificates |
| `GET` | `/api/blockchain/verify/{hash}/` | None | Direct blockchain verification |

### Example — Get JWT Token
```bash
POST /api/token/
{
    "username": "admin",
    "password": "your-password"
}
```

### Example — Issue Certificate
```bash
POST /api/issue/
Authorization: Bearer <access_token>

{
    "student_name": "John Doe",
    "course_name": "Cloud Engineering",
    "issue_date": "2026-07-27"
}
```

### Example Response
```json
{
    "certificate_id": "94b7b263-0840-4de3-90bb-51bc002e3724",
    "student_name": "John Doe",
    "course_name": "Cloud Engineering",
    "issue_date": "2026-07-27",
    "certificate_hash": "2501348c0f4df79...",
    "tx_hash": "3df496000f59c486...",
    "blockchain": "Ethereum (Ganache Local)",
    "anchored": true
}
```

---

## 🔐 Security Design

```
✅ SHA-256 hashing — any change in certificate data invalidates the hash
✅ JWT authentication — stateless, industry-standard API auth
✅ Role-based access — public/staff/admin separation
✅ Blockchain immutability — hashes cannot be deleted or modified
✅ Environment variables — no secrets in codebase
✅ Nginx reverse proxy — Django never exposed directly
```

---

## 📁 Project Structure

```
certchain/
├── certchain/              ← Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── certificates/           ← Main application
│   ├── models.py           ← Certificate + TransactionLog models
│   ├── views.py            ← UI views + staff dashboard
│   ├── api.py              ← REST API endpoints
│   ├── serializers.py      ← DRF serializers
│   ├── utils.py            ← SHA-256 hashing + email
│   ├── blockchain.py       ← Web3.py + smart contract
│   ├── contract.py         ← Solidity smart contract
│   ├── forms.py            ← Django forms
│   ├── admin.py            ← Django admin config
│   └── templates/          ← HTML templates
├── nginx/
│   └── nginx.conf          ← Nginx reverse proxy config
├── Dockerfile              ← Django container blueprint
├── docker-compose.yml      ← Multi-container orchestration
├── requirements.txt        ← Python dependencies
└── .env                    ← Environment variables (not committed)
```

---

## 👥 Staff Profiles (Demo)

| Username | Password | Role |
|----------|----------|------|
| sarah.johnson | Staff@1234 | Staff |
| david.chen | Staff@1234 | Staff |
| amara.diallo | Staff@1234 | Staff |
| lucas.silva | Staff@1234 | Staff |
| priya.sharma | Staff@1234 | Staff |

---

## 🎓 About This Project

Built by a 3rd year Computer Science & Engineering student from Mozambique studying in India. CertChain was designed as both a learning vehicle for cloud, blockchain, and backend engineering — and a real solution to a real problem.

**Shortlisted for university startup evaluation competition.**

### Skills Demonstrated
- Cloud deployment (AWS EC2)
- Docker containerization and orchestration
- Blockchain integration (Ethereum + Solidity + Web3.py)
- REST API design with JWT authentication
- Cryptographic hashing for data integrity
- PostgreSQL database design
- Nginx reverse proxy configuration
- Email notification systems
- Role-based access control

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 🔗 Connect

Built with 🔥 by **Taibo Junior**

[![GitHub](https://img.shields.io/badge/GitHub-TJunior03-181717?style=flat-square&logo=github)](https://github.com/TJunior03)
