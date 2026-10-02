# 🛡️ SecureFS: Secure Encrypted Filesystem Prototype

> **Project Title:** Designing Secure File Systems for Sensitive Data  
> **Domain:** Operating Systems & Cybersecurity (SIH 2026 / Academic Project)  
> **Language:** Python 3 (Pure Python with optional `cryptography` acceleration)  
> **Security Core:** AES-256-GCM • PBKDF2 Key Derivation • Instant Tamper Detection • DoD 3-Pass Shredding  

---

## 📖 Table of Contents
1. [What is SecureFS in Simple Words?](#-what-is-securefs-in-simple-words)
2. [Why Do We Need This? (The Real-World Problem)](#-why-do-we-need-this-the-real-world-problem)
3. [Key Features Explained Simply](#-key-features-explained-simply)
4. [How It Works (Under the Hood)](#-how-it-works-under-the-hood)
5. [The On-Disk File Structure (`.sfs`)](#-the-on-disk-file-structure-sfs)
6. [Project Structure](#-project-structure)
7. [Installation & Requirements](#-installation--requirements)
8. [Quick Start: Running the Interactive Demo](#-quick-start-running-the-interactive-demo)
9. [Step-by-Step Code Tutorial (How to Use SecureFS)](#-step-by-step-code-tutorial-how-to-use-securefs)
10. [Understanding the Audit Log (`audit.log`)](#-understanding-the-audit-log-auditlog)
11. [Standard Filesystems vs. SecureFS](#-standard-filesystems-vs-securefs)
12. [Frequently Asked Questions (FAQ)](#-frequently-asked-questions-faq)
13. [Future Scope & Roadmap](#-future-scope--roadmap)

---

## 💡 What is SecureFS in Simple Words?

Imagine keeping your secret documents in a transparent plastic folder on your desk. Anyone walking by can read them, photocopy them, change words with a pen, or steal them. This is how regular computer filesystems (like NTFS on Windows or ext4 on Linux) store your files by default—in plain, unencrypted text.

**SecureFS is like a high-tech digital bank vault for your files:**
- **Unreadable to Outsiders:** Every file you save is converted into scrambled gibberish (ciphertext). If someone takes the file or steals the hard drive, they cannot read a single letter.
- **Tamper-Evident Seal:** Like a security seal on medicine packaging, if anyone modifies even a single byte on the disk, SecureFS instantly spots it and locks them out.
- **Guaranteed Destruction:** When you delete a file, it doesn't just hide the name—it physically scribbles random data over the storage space 3 times, making recovery impossible even with forensic tools.
- **Flight Recorder (Audit Trail):** Every single action (reading, writing, deleting, or failed hacking attempts) is automatically recorded with exact timestamps.

---

## 🚨 Why Do We Need This? (The Real-World Problem)

| Normal Filesystem Weakness | What Actually Happens | How SecureFS Fixes It |
|---|---|---|
| **Plaintext Storage** | When you save `passwords.txt`, the actual words are sitting on the physical disk sectors. | **AES-256 Encryption:** Only encrypted scrambled bytes ever touch the physical disk. |
| **Offline Hard Drive Theft** | If a laptop is stolen, an attacker can take out the SSD, plug it into another PC, and bypass the operating system login screen completely. | **Zero Plaintext on Disk:** Without the secret passphrase, disk data remains completely unreadable math noise. |
| **Silent File Tampering** | Malware or a rogue user can modify an offline file (e.g., change banking details or system configs) without anyone noticing. | **Cryptographic MAC Tag:** Every file has a digital authentication tag. If even 1 bit changes, decryption immediately fails with a security alert. |
| **Fake "Delete" (Unlink)** | Clicking "Delete" only removes the filename pointer. The contents remain on disk and can be restored using recovery tools like Recuva. | **3-Pass DoD Shredding:** Overwrites the entire file with random bytes 3 times and forces a hardware sync (`fsync`) before removal. |
| **Lack of Tamper Auditing** | Normal logs don't record if an unauthorized person touched or corrupted an offline file. | **JSON-Lines Audit Log:** Logs every read, write, failed attempt, and tamper warning with ISO timestamps. |

---

## ✨ Key Features Explained Simply

### 1. 🔒 Military-Grade Encryption (AES-256-GCM)
Files are encrypted using **AES-256** in **Galois/Counter Mode (GCM)**. 
- **256-bit security** means there are $2^{256}$ possible keys. Even all the supercomputers in the world combined cannot crack this through guessing.
- Encryption and decryption happen purely inside the computer's memory (RAM). Plaintext is never written to disk.

### 2. 🛡️ Unbreakable Key Derivation (PBKDF2 with 100,000 Rounds)
Instead of using your human password directly, SecureFS puts it through an industrial-strength key stretching algorithm (**PBKDF2-HMAC-SHA256**) with **100,000 computational rounds** and a **unique 16-byte random salt**.
- This makes brute-force password guessing tools (running on fast GPUs) extremely slow and impractical.
- Even if two files have the same password, each gets a different salt, meaning they produce completely different encrypted files!

### 3. 🚨 Instant Tamper & Bit-Flip Detection
SecureFS uses **Authenticated Encryption with Associated Data (AEAD)**:
- Every time a file is saved, a 16-byte cryptographic verification tag (MAC) is calculated.
- When opening the file, SecureFS checks this tag *before* revealing any data.
- If even **one single byte** was altered by disk corruption, malware, or an attacker, the verification fails instantly, raises a `PermissionError`, and logs a security alarm.

### 4. 🌪️ 3-Pass Secure Shredding (DoD 5220.22-M Style)
When you delete a file through SecureFS:
1. It verifies your password to ensure you are authorized.
2. It overwrites the entire file on disk with random cryptographically secure bytes (`secrets.token_bytes`).
3. It repeats this overwrite **3 times**.
4. It calls `os.fsync()` after each pass to force the physical drive controller to flush its cache directly to physical storage.
5. Only then is the file removed from the filesystem.

### 5. 📜 Forensic Audit Logging (`audit.log`)
Every event is recorded in a machine-readable, append-only **JSON-Lines** file (`audit.log`). Each entry captures:
- Exact UTC timestamp (ISO-8601 format)
- Action attempted (`WRITE`, `READ`, `SECURE_DELETE`)
- Filename
- Status (`SUCCESS`, `FAILED`, `ALERT_TAMPER_OR_AUTH_FAIL`)
- Context details (payload size, error message, etc.)

---

## ⚙️ How It Works (Under the Hood)

### Writing / Saving a File:
```
User provides Plaintext + Secret Password
                │
                ▼
1. Generate fresh 16-byte random Salt
                │
                ▼
2. Derive 256-bit Key using PBKDF2 (100,000 rounds)
                │
                ▼
3. Generate fresh 12-byte random Nonce (IV)
                │
                ▼
4. Encrypt Plaintext via AES-256-GCM ──► produces Ciphertext + 16-byte Auth Tag
                │
                ▼
5. Pack together: [Salt (16B)] + [Nonce (12B)] + [Ciphertext + Auth Tag]
                │
                ▼
6. Save to disk as '<filename>.sfs' and record WRITE event in 'audit.log'
```

### Reading / Opening a File:
```
User requests File with Secret Password
                │
                ▼
1. Read packed .sfs container from disk
                │
                ▼
2. Unpack Salt (first 16 bytes) and Nonce (next 12 bytes)
                │
                ▼
3. Re-derive 256-bit Key using Password + Salt in RAM
                │
                ▼
4. Attempt AES-GCM Decryption & Authenticate Tag
         │                             │
    [Tag is Valid]              [Tag is Invalid / Modified]
         │                             │
         ▼                             ▼
Return original Plaintext       Stop immediately!
Log 'READ SUCCESS'              Raise PermissionError
                                Log 'ALERT_TAMPER_OR_AUTH_FAIL'
```

---

## 📦 The On-Disk File Structure (`.sfs`)

Each encrypted file saved by SecureFS is stored with a `.sfs` extension. It has a lightweight 28-byte header followed by the encrypted content and authentication tag:

```
┌─────────────────┬─────────────────┬──────────────────────────────────────────┐
│   Salt Header   │    GCM Nonce    │         Ciphertext + Auth Tag            │
│    (16 Bytes)   │   (12 Bytes)    │             (Variable Size)              │
├─────────────────┼─────────────────┼──────────────────────────────────────────┤
│ Offset: 0 to 15 │ Offset: 16 to 27│ Offset: 28 to End                        │
└─────────────────┴─────────────────┴──────────────────────────────────────────┘
```

> **Zero Sensitive Data Stored:**
> - Neither your password nor your encryption key is ever saved anywhere in the file or on the disk.
> - The salt and nonce are public random values required to recompute the key and decipher the stream. Without the password, they are mathematically useless to an attacker.

---

## 📁 Project Structure

```text
.
├── securefs.py                       # Core SecureFS vault implementation (~130 lines)
├── demo.py                           # Interactive presentation demo script (~90 lines)
├── generate_presentation.py          # Python script to generate PowerPoint presentation slides
├── SecureFS_Project_Presentation.pptx # Evaluator-ready 5-slide project presentation
├── encrypted_storage_demo/           # Demo vault folder containing generated .sfs files
├── audit_demo.log                    # Demonstration audit ledger output
└── README.md                         # Detailed project documentation (this file)
```

---

## 🚀 Installation & Requirements

### 1. Requirements
- **Python 3.7+** (Pre-installed on almost all Linux distributions, macOS, and modern Windows).
- **Cryptography library** (Recommended for hardware-accelerated AES-GCM):
  ```bash
  pip install cryptography
  ```

> 💡 **Zero Dependency Fallback:**  
> If `cryptography` is not installed on your system, SecureFS **will not crash!** It includes a built-in fallback using Python's standard library (`hashlib`, `hmac`, and `secrets`), ensuring it works anywhere out-of-the-box.

---

## 🖥️ Quick Start: Running the Interactive Demo

We have included a comprehensive demonstration script (`demo.py`) that showcases all security features step-by-step:

```bash
python3 demo.py
```

### What You Will See in the Demo:
1. **Writing a File:** Encrypts a sensitive project report (`confidential_project.txt`) into `encrypted_storage_demo/confidential_project.txt.sfs`.
2. **Disk Inspection:** Prints the raw hexadecimal bytes stored on disk, proving no plain English text exists on storage.
3. **Decryption:** Successfully decrypts and prints the original content using the correct password.
4. **Access Control Check:** Tries to read the file using an incorrect password (`HackerWrongPassword!`), demonstrating immediate rejection.
5. **Simulated Tamper Attack:** Deliberately modifies byte 25 on disk (simulating disk corruption or malware altering data). When decryption is attempted, SecureFS detects the broken integrity tag and aborts with a security alert!
6. **Audit Trail Review:** Prints the formatted audit log showing timestamps, actions, and security alerts.

---

## 💻 Step-by-Step Code Tutorial (How to Use SecureFS)

You can easily integrate SecureFS into any Python project:

### Step 1: Initialize the Vault
```python
from securefs import SecureFS

# Create a SecureFS instance with custom storage and log locations
fs = SecureFS(storage_dir="my_vault", log_file="my_audit.log")
```

### Step 2: Encrypt and Save a File
```python
# Sensitive data must be in bytes
secret_data = "Secret bank credentials: User=admin, Pass=SuperSecret123".encode("utf-8")
password = "MyStrongVaultPassword!"

# Write to encrypted storage
file_path = fs.write_file("credentials.txt", secret_data, password)
print(f"File saved securely at: {file_path}")
# Output: File saved securely at: my_vault/credentials.txt.sfs
```

### Step 3: Read and Decrypt a File
```python
try:
    decrypted_bytes = fs.read_file("credentials.txt", password)
    print("Decrypted content:", decrypted_bytes.decode("utf-8"))
except PermissionError:
    print("Access Denied: Wrong password or tampered file!")
except FileNotFoundError:
    print("Error: The requested file does not exist.")
```

### Step 4: Securely Shred and Delete a File
```python
# Requires the correct password before shredding to prevent unauthorized deletion
try:
    fs.secure_delete("credentials.txt", password)
    print("File shredded (3 passes) and removed completely!")
except PermissionError:
    print("Cannot delete: Authentication failed!")
```

---

## 📋 Understanding the Audit Log (`audit.log`)

Every file operation appends a JSON record. This format is directly compatible with modern Security Information and Event Management (SIEM) tools like Splunk or Elasticsearch.

### Example Log Entries:

```json
{"timestamp": "2026-10-02T12:35:10.123456Z", "action": "WRITE", "filename": "confidential_project.txt", "status": "SUCCESS", "details": "Encrypted size: 172 bytes"}
{"timestamp": "2026-10-02T12:35:10.134567Z", "action": "READ", "filename": "confidential_project.txt", "status": "SUCCESS", "details": "Decrypted 128 bytes"}
{"timestamp": "2026-10-02T12:35:10.145678Z", "action": "READ", "filename": "confidential_project.txt", "status": "ALERT_TAMPER_OR_AUTH_FAIL", "details": "MAC mismatch: file tampered or wrong password"}
{"timestamp": "2026-10-02T12:35:10.160123Z", "action": "SECURE_DELETE", "filename": "confidential_project.txt", "status": "SUCCESS", "details": "Shredded (3 passes) and removed"}
```

---

## 📊 Standard Filesystems vs. SecureFS

| Security Property | Standard Filesystem (ext4 / NTFS) | SecureFS Prototype |
|---|---|---|
| **Confidentiality at Rest** | ❌ None (Stored as plain text) | ✅ AES-256 Authenticated Encryption |
| **Protection Against Disk Theft** | ❌ Data readable when disk is moved | ✅ Data unreadable without password |
| **Bit-Level Integrity Check** | ❌ None (Silent file corruption) | ✅ 100% Tamper Detection via MAC |
| **Data Deletion Security** | ❌ Only metadata unlinked (Recoverable) | ✅ 3-Pass Random Overwrite + `fsync` |
| **Security Auditing** | ❌ Generic OS logs only | ✅ Real-time, tamper-flagged JSON ledger |
| **Setup Complexity** | High (Requires kernel modules / LUKS) | Minimal (Pure Python, single module) |

---

## ❓ Frequently Asked Questions (FAQ)

#### Q1: If someone copies my `.sfs` file to a USB stick, can they read it?
**No.** The file is encrypted with AES-256. Without the exact passphrase, the file looks like completely random noise and cannot be deciphered.

#### Q2: What happens if an attacker modifies just one letter inside the file?
The decryption algorithm mathematically checks the 128-bit authentication tag before releasing any data. If even a single bit of the file is changed, the tag check fails, the read is blocked, and an alarm is logged.

#### Q3: Why do we use a Salt if we already have a password?
If two users pick the password `Password123!`, without a salt, both files would generate identical keys and detectable patterns. A salt is a random 16-byte value added to the password. This guarantees that every encryption produces totally unique ciphertext, stopping hackers from using pre-calculated password tables (Rainbow Tables).

#### Q4: Why 3 passes for secure deletion instead of standard delete?
When you delete a file normally in an OS, the disk sectors are simply marked as "free to use," but the old data remains untouched until overwritten by new files. SecureFS actively writes random bytes across the entire file 3 times and executes `fsync()` to force the hard drive to commit those writes immediately.

---

## 🔮 Future Scope & Roadmap

- [ ] **FUSE Virtual Driver:** Mount SecureFS as a virtual Linux drive (e.g., `/mnt/securevault`), allowing any normal application (text editors, media players) to interact with files transparently.
- [ ] **Hardware TPM 2.0 Integration:** Bind the master encryption key to the machine's Trusted Platform Module (TPM) chip to ensure files can only be decrypted on authorized hardware.
- [ ] **Multi-User Key Sharing:** Add Public Key Cryptography (RSA-4096 / ECC) to allow sharing encrypted files between multiple authorized users without sharing master passwords.
- [ ] **GUI Dashboard:** A simple, modern desktop interface to drag-and-drop files into the vault and view real-time audit logs.

---

## 📄 License
This project is open-source and released under the [MIT License](LICENSE).
