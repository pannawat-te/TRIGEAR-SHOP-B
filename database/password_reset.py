# ไฟล์นี้: รับคำขอลืมรหัส อนุมัติรหัสชั่วคราว และบังคับเปลี่ยนรหัสใหม่
import secrets
import string
from datetime import datetime, timedelta
from database.database import get_connection, hash_password, verify_password

from database.password_policy import valid_password,PASSWORD_HINT

# def request_reset: ค้นหาบัญชีจาก Username/อีเมล และเพิ่มคำขอรอดำเนินการโดยไม่สร้างคำขอซ้ำ
def request_reset(username,email):
    conn=get_connection()
    try:
        with conn:
            row=conn.execute("SELECT id FROM users WHERE username=? AND lower(email)=lower(?)",(username.strip(),email.strip())).fetchone()
            if row:
                # Reuse a live approved request; allow a fresh request once its OTP expires.
                import time
                active=conn.execute("SELECT r.id FROM password_reset_requests r WHERE r.user_id=? AND r.status='otp_sent' AND EXISTS (SELECT 1 FROM email_otps o WHERE o.request_id=r.id AND o.state='sent' AND o.expires_at>?)",(row[0],time.time())).fetchone()
                if active:return
                conn.execute("UPDATE password_reset_requests SET status='expired' WHERE user_id=? AND status='otp_sent'",(row[0],))
                conn.execute("INSERT OR IGNORE INTO password_reset_requests(user_id) VALUES(?)",(row[0],))
    finally:conn.close()

# Admin verifies identity before approving an email OTP. Password stays unchanged until used.
def process_reset(request_id,admin_id,reject=False):
    from database.email_otp import issue
    conn=get_connection()
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            admin=conn.execute("SELECT role,must_change_password FROM users WHERE id=?",(admin_id,)).fetchone()
            if admin!=('admin',0):raise ValueError("เฉพาะ Admin ที่เข้าสู่ระบบแล้วเท่านั้น")
            row=conn.execute("SELECT r.user_id,u.email FROM password_reset_requests r JOIN users u ON u.id=r.user_id WHERE r.id=? AND r.status IN ('pending','otp_sent')",(request_id,)).fetchone()
            if not row:raise ValueError("คำขอนี้ดำเนินการแล้ว")
            if row[0]==admin_id:raise ValueError("ให้ Admin คนอื่นดำเนินการคำขอของคุณ")
            if reject:
                conn.execute("UPDATE email_otps SET state='revoked' WHERE request_id=? AND state IN ('sent','sending')",(request_id,))
                conn.execute("UPDATE password_reset_requests SET status='rejected',processed_at=CURRENT_TIMESTAMP,processed_by=? WHERE id=?",(admin_id,request_id))
                return None
        issue('reset',row[1],user_id=row[0],request_id=request_id)
        with conn:
            conn.execute("UPDATE password_reset_requests SET processed_by=?,processed_at=CURRENT_TIMESTAMP WHERE id=? AND status='otp_sent'",(admin_id,request_id))
        return True
    finally:conn.close()

# def change_required_password: ตรวจรหัสชั่วคราวและวันหมดอายุ แล้วบันทึกแฮชรหัสใหม่และปลดสถานะบังคับเปลี่ยน
def change_required_password(user_id,temporary,new_password):
    if not valid_password(new_password):raise ValueError(PASSWORD_HINT)
    if new_password==temporary:raise ValueError("กรุณาตั้งรหัสใหม่ที่ต่างจากรหัสชั่วคราว")
    conn=get_connection()
    try:
        with conn:
            row=conn.execute("SELECT password,must_change_password,temporary_password_expires FROM users WHERE id=?",(user_id,)).fetchone()
            if not row or not row[1] or not verify_password(temporary,row[0]):raise ValueError("รหัสชั่วคราวไม่ถูกต้อง")
            if not row[2] or datetime.fromisoformat(row[2])<=datetime.now():raise ValueError("รหัสชั่วคราวหมดอายุ กรุณาส่งคำขอใหม่")
            conn.execute("UPDATE users SET password=?,must_change_password=0,temporary_password_expires=NULL WHERE id=?",(hash_password(new_password),user_id))
    finally:conn.close()
