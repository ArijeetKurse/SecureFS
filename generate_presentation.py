#!/usr/bin/env python3
"""
Generate a high-contrast, strictly bullet-driven 5-slide presentation for SecureFS.
All bullet points use visible colored bullet glyphs guaranteed to render in LibreOffice & PowerPoint.
"""

import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------
# COLOR PALETTE
# ---------------------------------------------------------
BG_COLOR = RGBColor(15, 23, 42)        # Slate 900
CARD_BG = RGBColor(30, 41, 59)         # Slate 800
CARD_BORDER = RGBColor(51, 65, 85)     # Slate 700

CYAN_PRIMARY = RGBColor(56, 189, 248)  # Sky 400
EMERALD_GREEN = RGBColor(52, 211, 153) # Emerald 400
ROSE_RED = RGBColor(251, 113, 133)     # Rose 400
AMBER_ACCENT = RGBColor(251, 191, 36)  # Amber 400
PURPLE_ACCENT = RGBColor(167, 139, 250)# Purple 400

TEXT_TITLE = RGBColor(255, 255, 255)   # Pure White
TEXT_MUTED = RGBColor(148, 163, 184)   # Slate 400
TEXT_BODY = RGBColor(226, 232, 240)    # Slate 200

FONT_HEADING = "Arial"
FONT_BODY = "Arial"

def set_slide_background(slide, prs):
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_COLOR
    bg_shape.line.fill.background()
    return bg_shape

def add_header(slide, category_tag: str, title: str, subtitle: str, slide_num: int):
    # Category Tag Pill
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.3))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_right = tf_tag.margin_top = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = f"●  {category_tag.upper()}"
    p_tag.font.name = FONT_HEADING
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN_PRIMARY

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.55))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_TITLE

    # Subtitle
    if subtitle:
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.28), Inches(11.5), Inches(0.35))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(13)
        p_sub.font.color.rgb = TEXT_MUTED

    # Footer
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(10.0), Inches(0.3))
    tf_foot = footer_box.text_frame
    tf_foot.word_wrap = True
    tf_foot.margin_left = tf_foot.margin_right = tf_foot.margin_top = tf_foot.margin_bottom = 0
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = "SecureFS | OS Project SIH 2026: Designing Secure File Systems for Sensitive Data"
    p_foot.font.name = FONT_BODY
    p_foot.font.size = Pt(10)
    p_foot.font.color.rgb = RGBColor(100, 116, 139)

    # Slide Number
    num_box = slide.shapes.add_textbox(Inches(11.5), Inches(6.9), Inches(1.0), Inches(0.3))
    tf_num = num_box.text_frame
    tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = f"{slide_num:02d} / 05"
    p_num.font.name = FONT_BODY
    p_num.font.size = Pt(10)
    p_num.font.bold = True
    p_num.font.color.rgb = CYAN_PRIMARY

def create_card(slide, left, top, width, height, border_color=CARD_BORDER, bg_color=CARD_BG):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)
    return card

def add_bullet_item(tf, bold_label, text, bullet_color=CYAN_PRIMARY, font_size=11, space_after=6, symbol="•"):
    """
    Appends a visibly bulleted line guaranteed to display on all presentation software.
    """
    if len(tf.paragraphs) == 1 and not tf.paragraphs[0].text:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
        
    p.space_after = Pt(space_after)

    # Visible bullet glyph
    r_sym = p.add_run()
    r_sym.text = f"{symbol}  "
    r_sym.font.name = FONT_HEADING
    r_sym.font.size = Pt(font_size + 1)
    r_sym.font.bold = True
    r_sym.font.color.rgb = bullet_color

    # Bold label
    if bold_label:
        r_bold = p.add_run()
        r_bold.text = f"{bold_label} "
        r_bold.font.name = FONT_HEADING
        r_bold.font.size = Pt(font_size)
        r_bold.font.bold = True
        r_bold.font.color.rgb = TEXT_TITLE

    # Clean description
    r_text = p.add_run()
    r_text.text = text
    r_text.font.name = FONT_BODY
    r_text.font.size = Pt(font_size)
    r_text.font.bold = False
    r_text.font.color.rgb = TEXT_BODY

# Initialize Presentation (16:9)
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# =========================================================
# SLIDE 1: TITLE & EXECUTIVE OVERVIEW
# =========================================================
slide1 = prs.slides.add_slide(blank_layout)
set_slide_background(slide1, prs)

# Accent line
top_bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.7), Inches(2.2), Inches(0.06))
top_bar.fill.solid()
top_bar.fill.fore_color.rgb = CYAN_PRIMARY
top_bar.line.fill.background()

# Category Tag
badge = slide1.shapes.add_textbox(Inches(0.8), Inches(0.9), Inches(10), Inches(0.35))
tf_b = badge.text_frame
tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0
p_b = tf_b.paragraphs[0]
p_b.text = "OPERATING SYSTEMS & CYBERSECURITY | SIH 2026"
p_b.font.name = FONT_HEADING
p_b.font.size = Pt(12)
p_b.font.bold = True
p_b.font.color.rgb = CYAN_PRIMARY

# Project Title
tbox = slide1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.8), Inches(1.35))
tf_t = tbox.text_frame
tf_t.word_wrap = True
tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
p1 = tf_t.paragraphs[0]
p1.text = "Designing Secure File Systems"
p1.font.name = FONT_HEADING
p1.font.size = Pt(36)
p1.font.bold = True
p1.font.color.rgb = TEXT_TITLE

p2 = tf_t.add_paragraph()
p2.text = "for Sensitive Data (SecureFS)"
p2.font.name = FONT_HEADING
p2.font.size = Pt(36)
p2.font.bold = True
p2.font.color.rgb = CYAN_PRIMARY

# Subtitle
desc_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.85), Inches(11.733), Inches(0.6))
tf_d = desc_box.text_frame
tf_d.word_wrap = True
tf_d.margin_left = tf_d.margin_right = tf_d.margin_top = tf_d.margin_bottom = 0
p_d = tf_d.paragraphs[0]
p_d.text = "A lightweight, tamper-proof encrypted file vault prototype combining modern AES-256-GCM cryptography, " \
           "PBKDF2 key derivation, instant integrity alarms, and DoD-grade secure shredding."
p_d.font.name = FONT_BODY
p_d.font.size = Pt(14)
p_d.font.color.rgb = TEXT_BODY

# 3 Feature Cards
features = [
    ("AES-256-GCM Vault", "Authenticated Encryption", CYAN_PRIMARY, [
        ("Galois/Counter Mode:", "Military-grade high-speed cipher"),
        ("Zero Plaintext on Disk:", "Stores only randomized ciphertext"),
        ("128-bit MAC Tag:", "Verifies authenticity & detects tampering"),
        ("Unique 12B Nonces:", "Stops replay & pattern recognition attacks")
    ]),
    ("Hardened Key Derivation", "PBKDF2-HMAC-SHA256", EMERALD_GREEN, [
        ("100,000 Rounds:", "Thwarts GPU brute-force attacks"),
        ("16-Byte Random Salt:", "Unique per file; foils rainbow tables"),
        ("In-Memory Only:", "Keys derived in RAM and cleared instantly"),
        ("Zero Key Retention:", "No credentials ever written to disk")
    ]),
    ("Active Tamper Defense", "Integrity & Shredding", ROSE_RED, [
        ("Bit-Flip Detection:", "Any disk alteration blocks file reads"),
        ("Permission Lockout:", "Immediate PermissionError exception"),
        ("Forensic Audit Log:", "ISO timestamped JSON-lines trail"),
        ("3-Pass DoD Shred:", "Random data overwrite + physical fsync")
    ])
]

card_w = Inches(3.64)
card_h = Inches(2.8)
gap = Inches(0.4)
start_x = Inches(0.8)
start_y = Inches(3.75)

for i, (f_title, f_sub, color, bullets) in enumerate(features):
    x = start_x + i * (card_w + gap)
    create_card(slide1, x, start_y, card_w, card_h, border_color=CARD_BORDER)
    
    dot = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + Inches(0.25), start_y + Inches(0.2), Inches(0.5), Inches(0.04))
    dot.fill.solid()
    dot.fill.fore_color.rgb = color
    dot.line.fill.background()

    tb = slide1.shapes.add_textbox(x + Inches(0.25), start_y + Inches(0.3), card_w - Inches(0.5), card_h - Inches(0.4))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = f_title
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = TEXT_TITLE

    p_sub_t = tf.add_paragraph()
    p_sub_t.text = f_sub
    p_sub_t.font.name = FONT_BODY
    p_sub_t.font.size = Pt(11)
    p_sub_t.font.bold = True
    p_sub_t.font.color.rgb = color
    p_sub_t.space_after = Pt(10)

    for bold_p, txt in bullets:
        add_bullet_item(tf, bold_p, txt, bullet_color=color, font_size=10.5, space_after=6, symbol="•")

# Slide 1 Footer
num_box = slide1.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(11.733), Inches(0.3))
tf_num = num_box.text_frame
p_num = tf_num.paragraphs[0]
p_num.text = "Prototype Implementation: Python 3 Vault Engine  •  Slide 01 / 05"
p_num.font.name = FONT_BODY
p_num.font.size = Pt(10)
p_num.font.color.rgb = RGBColor(100, 116, 139)


# =========================================================
# SLIDE 2: PROBLEM STATEMENT & SECURITY OBJECTIVES
# =========================================================
slide2 = prs.slides.add_slide(blank_layout)
set_slide_background(slide2, prs)
add_header(slide2, "Threat Landscape & Goals", "Problem Statement & Security Objectives",
           "Addressing the critical security gaps in default operating system filesystems.", 2)

col_w = Inches(5.67)
col_h = Inches(4.9)
col1_x = Inches(0.8)
col2_x = Inches(6.86)
content_y = Inches(1.8)

# Left Column: Vulnerabilities
create_card(slide2, col1_x, content_y, col_w, col_h, border_color=ROSE_RED)
tb_p = slide2.shapes.add_textbox(col1_x + Inches(0.3), content_y + Inches(0.25), col_w - Inches(0.6), col_h - Inches(0.5))
tf_p = tb_p.text_frame
tf_p.word_wrap = True
tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0

p = tf_p.paragraphs[0]
p.text = "STANDARD OS FILESYSTEM FLAWS"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = ROSE_RED
p.space_after = Pt(14)

vulns_bullets = [
    ("Plaintext Storage at Rest:", "ext4 & NTFS save files unencrypted; drive theft exposes data."),
    ("Offline Drive Mounting:", "Attacker mounting the disk externally bypasses OS permissions."),
    ("Silent Data Tampering:", "Filesystems lack cryptographic tags; undetected malware alters files."),
    ("Corrupted Execution:", "Modified system files execute without integrity verification."),
    ("Insecure Deletion (Unlink):", "Standard delete only removes pointers; data stays on disk."),
    ("Forensic Recoverability:", "Deleted sensitive records are trivial to recover with basic tools."),
    ("Unverified Logging:", "Generic system logs lack tamper alarms and per-file cryptographic tracking.")
]

for b_hdr, b_txt in vulns_bullets:
    add_bullet_item(tf_p, b_hdr, b_txt, bullet_color=ROSE_RED, font_size=11, space_after=8, symbol="•")

# Right Column: Objectives
create_card(slide2, col2_x, content_y, col_w, col_h, border_color=EMERALD_GREEN)
tb_s = slide2.shapes.add_textbox(col2_x + Inches(0.3), content_y + Inches(0.25), col_w - Inches(0.6), col_h - Inches(0.5))
tf_s = tb_s.text_frame
tf_s.word_wrap = True
tf_s.margin_left = tf_s.margin_right = tf_s.margin_top = tf_s.margin_bottom = 0

p = tf_s.paragraphs[0]
p.text = "SECUREFS SECURITY OBJECTIVES"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = EMERALD_GREEN
p.space_after = Pt(14)

goals_bullets = [
    ("Encrypted Storage:", "Every file is encrypted before disk write; raw disk has only ciphertext."),
    ("Full Confidentiality:", "AES-256 ensures zero data exposure even during offline drive theft."),
    ("Real-Time Tamper Alarm:", "Authenticated AEAD tags immediately detect any modified byte."),
    ("Instant Read Lockout:", "Corrupted payloads trigger PermissionError and abort immediately."),
    ("DoD-Grade Shredding:", "3-pass random data overwrite with os.fsync() forces hardware flush."),
    ("Zero Data Remanence:", "Completely sanitizes disk sectors before filesystem unlinking."),
    ("Immutable Audit Trail:", "Appends every read, write, tamper alert, and delete to JSON log.")
]

for b_hdr, b_txt in goals_bullets:
    add_bullet_item(tf_s, b_hdr, b_txt, bullet_color=EMERALD_GREEN, font_size=11, space_after=8, symbol="•")


# =========================================================
# SLIDE 3: SYSTEM ARCHITECTURE & CRYPTOGRAPHIC ENGINE
# =========================================================
slide3 = prs.slides.add_slide(blank_layout)
set_slide_background(slide3, prs)
add_header(slide3, "Cryptographic Engineering", "System Architecture & Cryptographic Engine",
           "Layered defense combining key derivation, authenticated encryption, and sealed container layout.", 3)

# Top Pipeline Card
pipe_card = create_card(slide3, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.35), border_color=CYAN_PRIMARY)
tb_pipe = slide3.shapes.add_textbox(Inches(1.0), Inches(1.92), Inches(11.333), Inches(1.1))
tf_pipe = tb_pipe.text_frame
tf_pipe.word_wrap = True
tf_pipe.margin_left = tf_pipe.margin_right = tf_pipe.margin_top = tf_pipe.margin_bottom = 0

p = tf_pipe.paragraphs[0]
p.text = "CRYPTOGRAPHIC PIPELINE FLOW"
p.font.name = FONT_HEADING
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = CYAN_PRIMARY
p.space_after = Pt(4)

add_bullet_item(tf_pipe, "Write Pipeline:", "Plaintext + Passphrase ──► PBKDF2 (100k it., 16B Salt) ──► AES-256-GCM ──► .sfs Vault File",
                bullet_color=CYAN_PRIMARY, font_size=11, space_after=4, symbol="•")
add_bullet_item(tf_pipe, "Read Pipeline:", ".sfs Vault File ──► Extract Salt & Nonce ──► Derive Key in RAM ──► Verify MAC ──► Plaintext",
                bullet_color=EMERALD_GREEN, font_size=11, space_after=4, symbol="•")
add_bullet_item(tf_pipe, "Memory Safety:", "Decryption occurs strictly in RAM; keys and plaintexts are cleared after use",
                bullet_color=AMBER_ACCENT, font_size=10.5, space_after=0, symbol="•")

# Bottom Left: Cryptographic Primitives
c_left_w = Inches(5.67)
c_left_h = Inches(3.4)
create_card(slide3, Inches(0.8), Inches(3.3), c_left_w, c_left_h)
tb_cp = slide3.shapes.add_textbox(Inches(1.0), Inches(3.42), c_left_w - Inches(0.4), c_left_h - Inches(0.25))
tf_cp = tb_cp.text_frame
tf_cp.word_wrap = True
tf_cp.margin_left = tf_cp.margin_right = tf_cp.margin_top = tf_cp.margin_bottom = 0

p = tf_cp.paragraphs[0]
p.text = "CRYPTOGRAPHIC PRIMITIVES & SPECS"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = CYAN_PRIMARY
p.space_after = Pt(10)

crypto_bullets = [
    ("Key Derivation:", "PBKDF2-HMAC-SHA256 (Generates 256-bit symmetric key)"),
    ("Iteration Count:", "100,000 computational rounds to mitigate brute-force"),
    ("Salt Generation:", "16-byte random salt generated via CSPRNG (secrets.token_bytes)"),
    ("Symmetric Cipher:", "AES-256-GCM (Authenticated Encryption with Associated Data)"),
    ("Nonce / IV:", "12-byte unique initialization vector per write operation"),
    ("MAC Auth Tag:", "128-bit cryptographic tag verifies message authenticity"),
    ("Fallback Mode:", "SHA-256 CTR keystream cipher with HMAC-SHA256 integrity")
]

for b_hdr, b_txt in crypto_bullets:
    add_bullet_item(tf_cp, b_hdr, b_txt, bullet_color=CYAN_PRIMARY, font_size=10.5, space_after=5, symbol="•")

# Bottom Right: On-Disk Container Binary Format
c_right_x = Inches(6.86)
create_card(slide3, c_right_x, Inches(3.3), c_left_w, c_left_h)
tb_df = slide3.shapes.add_textbox(c_right_x + Inches(0.2), Inches(3.42), c_left_w - Inches(0.4), c_left_h - Inches(0.25))
tf_df = tb_df.text_frame
tf_df.word_wrap = True
tf_df.margin_left = tf_df.margin_right = tf_df.margin_top = tf_df.margin_bottom = 0

p = tf_df.paragraphs[0]
p.text = "ON-DISK BINARY FORMAT (.sfs FILE)"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = EMERALD_GREEN
p.space_after = Pt(10)

layout_bullets = [
    ("Bytes [00 : 16] - Salt Header:", "Stored at file head; used with passphrase to re-derive key"),
    ("Bytes [16 : 28] - GCM Nonce:", "Unique initialization vector required for AES-GCM decryption"),
    ("Bytes [28 : End] - Ciphertext + Tag:", "Encrypted data payload sealed with 16-byte MAC tag"),
    ("Zero Secret Storage:", "No passwords or keys are ever stored in the container"),
    ("Tamper Sensitivity:", "Altering even 1 bit makes tag verification mathematically fail"),
    ("Collision Resistance:", "Unique per-file salts guarantee unique ciphertext outputs"),
    ("Fixed Overhead:", "Only 44 bytes of security metadata per file")
]

for b_hdr, b_txt in layout_bullets:
    add_bullet_item(tf_df, b_hdr, b_txt, bullet_color=EMERALD_GREEN, font_size=10.5, space_after=5, symbol="•")


# =========================================================
# SLIDE 4: CORE IMPLEMENTATION & VERIFICATION MECHANICS
# =========================================================
slide4 = prs.slides.add_slide(blank_layout)
set_slide_background(slide4, prs)
add_header(slide4, "Implementation & Security Modules", "Core Features & Verification Mechanics",
           "Modular components ensuring confidentiality, proactive integrity defense, and traceability.", 4)

grid_w = Inches(5.67)
grid_h = Inches(2.35)
col1 = Inches(0.8)
col2 = Inches(6.86)
row1 = Inches(1.8)
row2 = Inches(4.35)

cards_data = [
    (col1, row1, "1. Transparent Read & Write Pipeline", CYAN_PRIMARY, [
        ("Simple File API:", "write_file() and read_file() programmatic abstractions"),
        ("Dynamic Derivation:", "Keys generated in memory on the fly; never stored on disk"),
        ("Fresh Random Seeds:", "Independent 16B salt & 12B nonce on every write operation"),
        ("Safe Cleanup:", "Sensitive memory buffers freed immediately after I/O finishes")
    ]),
    (col2, row1, "2. Proactive Tamper Detection & Alerts", ROSE_RED, [
        ("Pre-Read Verification:", "Validates cryptographic MAC tag before decrypting plaintext"),
        ("Bit-Flip Defense:", "Single altered byte on disk triggers immediate PermissionError"),
        ("Active Containment:", "Halts execution to prevent corrupt data entering OS processes"),
        ("CCA Protection:", "Immunizes against Chosen-Ciphertext Attacks and malicious injections")
    ]),
    (col1, row2, "3. Forensic Audit Ledger (audit.log)", AMBER_ACCENT, [
        ("JSON-Lines Format:", "Structured, append-only entries suitable for automated analysis"),
        ("Precise Timestamps:", "ISO 8601 UTC timestamps logged on every system operation"),
        ("Comprehensive Scope:", "Tracks WRITE, READ, SUCCESS, TAMPER_ALERT, and SECURE_DELETE"),
        ("SIEM Compatibility:", "Directly ingestible into enterprise SIEMs (Splunk, Elastic)")
    ]),
    (col2, row2, "4. DoD-Grade Secure File Deletion", EMERALD_GREEN, [
        ("Authentication Gate:", "Requires valid passphrase authentication before allowing delete"),
        ("3-Pass Cryptographic Shred:", "Overwrites entire file allocation 3 times with CSPRNG bytes"),
        ("Hardware Sync (fsync):", "Calls os.fsync() to force controller cache flush to media"),
        ("Forensic Clean Removal:", "Unlinks file pointer with zero recoverable data remanence")
    ])
]

for left, top, c_title, color, bullet_list in cards_data:
    create_card(slide4, left, top, grid_w, grid_h, border_color=CARD_BORDER)
    
    tb = slide4.shapes.add_textbox(left + Inches(0.25), top + Inches(0.18), grid_w - Inches(0.5), grid_h - Inches(0.25))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = c_title
    p.font.name = FONT_HEADING
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = color
    p.space_after = Pt(6)

    for b_title, b_desc in bullet_list:
        add_bullet_item(tf, b_title, b_desc, bullet_color=color, font_size=10.5, space_after=4, symbol="•")


# =========================================================
# SLIDE 5: DEMONSTRATION, EVALUATION & ROADMAP
# =========================================================
slide5 = prs.slides.add_slide(blank_layout)
set_slide_background(slide5, prs)
add_header(slide5, "Verification & Future Scope", "Live Demo Results & Future Roadmap",
           "Empirical evaluation results and upcoming architecture enhancements.", 5)

col_w = Inches(5.67)
col_h = Inches(4.9)
col1_x = Inches(0.8)
col2_x = Inches(6.86)
content_y = Inches(1.8)

# Left Column: Demo Workflow
create_card(slide5, col1_x, content_y, col_w, col_h, border_color=CYAN_PRIMARY)
tb_d = slide5.shapes.add_textbox(col1_x + Inches(0.3), content_y + Inches(0.22), col_w - Inches(0.6), col_h - Inches(0.4))
tf_d = tb_d.text_frame
tf_d.word_wrap = True
tf_d.margin_left = tf_d.margin_right = tf_d.margin_top = tf_d.margin_bottom = 0

p = tf_d.paragraphs[0]
p.text = "DEMO VERIFICATION WORKFLOW (demo.py)"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = CYAN_PRIMARY
p.space_after = Pt(10)

demo_bullets = [
    ("Step 1 - Encrypted Write:", "Encrypted 'confidential_project.txt' and created .sfs file"),
    ("Step 2 - Disk Inspection:", "Verified raw hex; proved zero plaintext readable on disk"),
    ("Step 3 - Transparent Read:", "Decrypted file using correct password with 100% data fidelity"),
    ("Step 4 - Auth Challenge:", "Supplied invalid password; access rejected via PermissionError"),
    ("Step 5 - Tamper Attack Test:", "Flipped bit 25 directly in raw disk file simulating malware"),
    ("Step 6 - Integrity Alarm:", "AEAD MAC check failed instantly; triggered ALERT_TAMPER log"),
    ("Step 7 - Audit Inspection:", "Printed structured JSON-lines log displaying complete audit trail")
]

for b_hdr, b_txt in demo_bullets:
    add_bullet_item(tf_d, b_hdr, b_txt, bullet_color=CYAN_PRIMARY, font_size=10.5, space_after=6, symbol="•")

# Right Column: Metrics & Roadmap
create_card(slide5, col2_x, content_y, col_w, col_h, border_color=PURPLE_ACCENT)
tb_r = slide5.shapes.add_textbox(col2_x + Inches(0.3), content_y + Inches(0.22), col_w - Inches(0.6), col_h - Inches(0.4))
tf_r = tb_r.text_frame
tf_r.word_wrap = True
tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

p = tf_r.paragraphs[0]
p.text = "EVALUATION METRICS & FUTURE ROADMAP"
p.font.name = FONT_HEADING
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = PURPLE_ACCENT
p.space_after = Pt(8)

# Metrics Sub-block
p_m_hdr = tf_r.add_paragraph()
p_m_hdr.text = "PROTOTYPE PERFORMANCE BENCHMARKS"
p_m_hdr.font.name = FONT_HEADING
p_m_hdr.font.size = Pt(11)
p_m_hdr.font.bold = True
p_m_hdr.font.color.rgb = AMBER_ACCENT
p_m_hdr.space_after = Pt(3)

metrics_bullets = [
    ("Tamper Detection Rate:", "100.0% (Guaranteed by 128-bit cryptographic MAC verification)"),
    ("Plaintext Remanence:", "0.0% (Eliminated via 3-pass DoD cryptographic overwrite + fsync)"),
    ("Key Derivation Overhead:", "~65ms per derivation (Tunable security work factor)")
]

for b_hdr, b_txt in metrics_bullets:
    add_bullet_item(tf_r, b_hdr, b_txt, bullet_color=AMBER_ACCENT, font_size=10.5, space_after=3, symbol="•")

# Spacing
p_space = tf_r.add_paragraph()
p_space.space_after = Pt(6)

# Roadmap Sub-block
p_rd_hdr = tf_r.add_paragraph()
p_rd_hdr.text = "FUTURE RESEARCH & PRODUCTION ROADMAP"
p_rd_hdr.font.name = FONT_HEADING
p_rd_hdr.font.size = Pt(11)
p_rd_hdr.font.bold = True
p_rd_hdr.font.color.rgb = EMERALD_GREEN
p_rd_hdr.space_after = Pt(3)

roadmap_bullets = [
    ("FUSE Virtual Mount:", "Mount as standard Linux filesystem (/mnt/securefs) for app access"),
    ("Hardware TPM 2.0 / HSM:", "Bind encryption root keys to TPM PCR registers to prevent theft"),
    ("Multi-User RBAC & Keys:", "Combine RSA-4096 / ECC asymmetric keys for multi-user sharing")
]

for b_hdr, b_txt in roadmap_bullets:
    add_bullet_item(tf_r, b_hdr, b_txt, bullet_color=EMERALD_GREEN, font_size=10.5, space_after=4, symbol="•")

# Save Presentation
output_path = "SecureFS_Project_Presentation.pptx"
prs.save(output_path)
print(f"[+] Presentation updated successfully at: {output_path}")
