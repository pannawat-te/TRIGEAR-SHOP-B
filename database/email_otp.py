"""Persistent one-use OTPs, scoped by purpose and recipient."""
import hashlib
import hmac
import json
import secrets
import time
from database.database import get_connection
from services.email_sender import send_otp

def create_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS email_otps (
        id TEXT PRIMARY KEY, purpose TEXT NOT NULL, recipient TEXT NOT NULL,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        request_id INTEGER REFERENCES password_reset_requests(id) ON DELETE CASCADE,
        payload TEXT NOT NULL DEFAULT '{}', code_hash TEXT NOT NULL,
        created_at REAL NOT NULL, expires_at REAL NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT 'sending')''')

def digest(token, code):
    return hashlib.pbkdf2_hmac('sha256', code.encode(), token.encode(), 120000).hex()

def issue(purpose, recipient, payload=None, user_id=None, request_id=None):
    token, code = secrets.token_hex(24), f'{secrets.randbelow(1000000):06d}'
    now = time.time()
    conn = get_connection()
    try:
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute("UPDATE email_otps SET payload='{}' WHERE expires_at<=? OR state IN ('used','failed','superseded','revoked')",(now,))
            # Reserve before sending to prevent concurrent sends bypassing cooldown.
            latest = conn.execute('SELECT created_at FROM email_otps WHERE purpose=? AND lower(recipient)=lower(?) ORDER BY created_at DESC LIMIT 1', (purpose, recipient)).fetchone()
            if latest and now-latest[0] < 60:
                raise ValueError('กรุณารออย่างน้อย 60 วินาทีก่อนส่ง OTP อีกครั้ง')
            if purpose == 'reset':
                row = conn.execute("SELECT user_id,status FROM password_reset_requests WHERE id=?", (request_id,)).fetchone()
                if not row or row[0] != user_id or row[1] not in ('pending','otp_sent'):
                    raise ValueError('คำขอนี้ดำเนินการแล้ว กรุณาส่งคำขอใหม่')
            conn.execute("UPDATE email_otps SET state='superseded' WHERE purpose=? AND lower(recipient)=lower(?) AND state IN ('sent','sending')", (purpose, recipient))
            conn.execute('INSERT INTO email_otps(id,purpose,recipient,user_id,request_id,payload,code_hash,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?)',
                         (token,purpose,recipient,user_id,request_id,json.dumps(payload or {}),digest(token,code),now,now+600))
        try:
            send_otp(recipient, code, purpose)
        except Exception:
            with conn: conn.execute("UPDATE email_otps SET state='failed' WHERE id=?", (token,))
            raise
        with conn:
            # A newer send or rejection must never reactivate this token.
            changed = conn.execute("UPDATE email_otps SET state='sent',expires_at=? WHERE id=? AND state='sending'", (time.time()+600,token)).rowcount
            if not changed: raise ValueError('OTP ถูกยกเลิกแล้ว กรุณาส่งคำขอใหม่')
            if request_id:
                conn.execute("UPDATE password_reset_requests SET status='otp_sent' WHERE id=? AND status IN ('pending','otp_sent')",(request_id,))
        return token
    finally:
        conn.close()

def consume(conn, token, purpose, code):
    row = conn.execute('SELECT recipient,user_id,request_id,payload,code_hash,expires_at,attempts,state FROM email_otps WHERE id=? AND purpose=?', (token,purpose)).fetchone()
    if not row or row[7] != 'sent': return None, 'OTP นี้ใช้ไม่ได้หรือถูกใช้แล้ว'
    if row[5] <= time.time(): return None, 'OTP หมดอายุ กรุณาขอรหัสใหม่'
    if row[6] >= 5: return None, 'กรอกผิดครบ 5 ครั้ง กรุณาขอ OTP ใหม่'
    if not hmac.compare_digest(digest(token,code.strip()),row[4]):
        conn.execute('UPDATE email_otps SET attempts=attempts+1 WHERE id=?',(token,))
        return None, 'OTP ไม่ถูกต้อง'
    conn.execute("UPDATE email_otps SET state='used',payload='{}' WHERE id=?",(token,))
    return row, None

def start_registration(username,email,password_hash,phone):
    conn = get_connection()
    try:
        if conn.execute('SELECT 1 FROM users WHERE username=? OR lower(email)=lower(?)',(username,email)).fetchone():
            raise ValueError('Username หรืออีเมลนี้ถูกใช้งานแล้ว')
    finally: conn.close()
    return issue('register',email,{'username':username,'password':password_hash,'phone':phone})

def finish_registration(token, code):
    conn = get_connection()
    error = None
    try:
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            row,error = consume(conn,token,'register',code)
            if row:
                data = json.loads(row[3])
                if conn.execute('SELECT 1 FROM users WHERE username=? OR lower(email)=lower(?)',(data['username'],row[0])).fetchone():
                    error = 'Username หรืออีเมลนี้ถูกใช้งานแล้ว กรุณาสมัครใหม่'
                else:
                    conn.execute("INSERT INTO users(username,email,password,role,contact_phone) VALUES(?,?,?,'customer',?)",(data['username'],row[0],data['password'],data['phone']))
        if error: raise ValueError(error)
    finally: conn.close()

def finish_reset(username,email,code,password):
    from database.database import hash_password
    from database.password_policy import valid_password,PASSWORD_HINT
    if not valid_password(password): raise ValueError(PASSWORD_HINT)
    conn = get_connection()
    error = None
    try:
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            found = conn.execute("SELECT o.id FROM email_otps o JOIN users u ON u.id=o.user_id WHERE u.username=? AND lower(u.email)=lower(?) AND lower(o.recipient)=lower(u.email) AND o.purpose='reset' AND o.state='sent' ORDER BY o.created_at DESC LIMIT 1",(username.strip(),email.strip())).fetchone()
            row,error = consume(conn,found[0] if found else '', 'reset',code)
            if row:
                request = conn.execute('SELECT status FROM password_reset_requests WHERE id=?',(row[2],)).fetchone()
                if not request or request[0] != 'otp_sent': error = 'คำขอถูกยกเลิกแล้ว'
                else:
                    conn.execute('UPDATE users SET password=?,must_change_password=0,temporary_password_expires=NULL WHERE id=?',(hash_password(password),row[1]))
                    conn.execute("UPDATE password_reset_requests SET status='completed',processed_at=CURRENT_TIMESTAMP WHERE id=?",(row[2],))
        if error: raise ValueError(error)
    finally: conn.close()
