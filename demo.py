#!/usr/bin/env python3
"""
SecureFS Demo Script for Project Evaluation / Presentation
"""

import os
import json
import time
from securefs import SecureFS

def banner(title):
    print("\n" + "=" * 60)
    print(f"   {title}")
    print("=" * 60)

def main():
    banner("SECURE ENCRYPTED FILESYSTEM — DEMO")
    
    PASSWORD = "MySecretCollegePassword123!"
    WRONG_PASSWORD = "HackerWrongPassword!"
    
    fs = SecureFS(storage_dir="encrypted_storage_demo", log_file="audit_demo.log")
    
    # 1. Store a sensitive file
    banner("1. Writing Sensitive File to Encrypted Filesystem")
    filename = "confidential_project.txt"
    content = (
        "CONFIDENTIAL PROJECT REPORT\n"
        "Project: Secure Filesystem Prototype\n"
        "Student ID: 2026-CS-SEC-01\n"
        "Status: Passed Evaluation with 100% Integrity.\n"
    ).encode('utf-8')
    
    path = fs.write_file(filename, content, PASSWORD)
    print(f"[+] File written successfully to storage path: {path}")
    
    # 2. Show raw encrypted content on disk
    banner("2. Inspecting Raw File on Disk (Disk Security Check)")
    with open(path, "rb") as f:
        raw_bytes = f.read()
    print(f"[!] Raw file size on disk: {len(raw_bytes)} bytes")
    print(f"[!] Raw Hex Preview (First 48 bytes): {raw_bytes[:48].hex()}")
    print("[✓] Notice: Raw disk contents are completely encrypted ciphertext & salt!")
    
    # 3. Read & Decrypt file with correct password
    banner("3. Transparent Decryption (Correct Password)")
    decrypted = fs.read_file(filename, PASSWORD)
    print("[+] Decrypted Payload Output:")
    print("-" * 40)
    print(decrypted.decode('utf-8'))
    print("-" * 40)

    # 4. Attempt Access with Wrong Password
    banner("4. Access Control Check (Wrong Password)")
    try:
        fs.read_file(filename, WRONG_PASSWORD)
    except PermissionError as e:
        print(f"[✓] EXPECTED SECURITY BEHAVIOR: {e}")

    # 5. Simulate Attacker Tampering on Raw Disk File
    banner("5. Integrity Verification (Simulating Disk File Tampering)")
    print("[!] Modifying byte 25 on the encrypted disk file (simulating malware/tampering)...")
    with open(path, "r+b") as f:
        f.seek(25)
        byte = f.read(1)
        f.seek(25)
        f.write(bytes([byte[0] ^ 0xFF]))  # flip bits
        
    try:
        fs.read_file(filename, PASSWORD)
    except PermissionError as e:
        print(f"[✓] EXPECTED SECURITY ALERT: {e}")

    # 6. Display Audit Log
    banner("6. Audit Log Inspection")
    print("Log Entries (JSON Format):")
    print("-" * 60)
    with open("audit_demo.log", "r") as f:
        for line in f:
            entry = json.loads(line)
            print(f"[{entry['timestamp']}] {entry['action']:<15} | Status: {entry['status']:<25} | {entry['details']}")
    print("-" * 60)

    banner("DEMO COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

