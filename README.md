# Secure Encrypted Filesystem Prototype

**Project Title:** Designing Secure File Systems for Sensitive Data  
**Language:** Python 3  
**Architecture:** Lightweight Encrypted File Vault (AES-GCM + PBKDF2 + HMAC)

---

## Features

1. **Transparent Encryption & Decryption**: File contents are encrypted using AES-256-GCM / PBKDF2 key derivation.
2. **Integrity & Tamper Protection**: Authenticated encryption detects any unauthorized byte modification on disk.
3. **Audit Logging**: JSON-lines audit trail (`audit.log`) records `WRITE`, `READ`, `AUTH_FAIL`, and `TAMPER_ALERT` events with ISO timestamps.
4. **Secure Deletion**: Overwrites target file with random data 3 times before unlinking from storage.

---

## Project Structure

```
.
├── securefs.py       # Core SecureFS Vault implementation (~140 lines)
├── demo.py           # Interactive presentation demo script (~60 lines)
└── README.md         # Project documentation
```

---

## How to Run the Demo

Run the interactive presentation script:

```bash
python3 demo.py
```

### Expected Output:
1. Encrypts and writes `confidential_project.txt`.
2. Shows raw encrypted bytes on disk (`encrypted_storage_demo/`).
3. Decrypts and prints plaintext using the correct password.
4. Rejects decryption with wrong password.
5. Bit-flips the encrypted file on disk and triggers an **Integrity Verification Alert**.
6. Displays the formatted JSON `audit_demo.log`.
