# ไฟล์นี้: อ่านข้อมูลสมาชิกและประวัติ โดยตรวจสิทธิ์ Admin ก่อนเข้าถึง
from database.database import get_connection

# def require_admin: ตรวจบทบาท Admin และสถานะบังคับเปลี่ยนรหัส; ปฏิเสธสิทธิ์ที่ไม่ถูกต้อง
def require_admin(conn,admin_id):
    row=conn.execute('SELECT role,must_change_password,is_blocked FROM users WHERE id=?',(admin_id,)).fetchone()
    if row!=('admin',0,0):raise ValueError('ต้องเข้าสู่ระบบด้วยบัญชี Admin')

# def list_members: ค้นหาสมาชิกด้วย Username/อีเมล/เบอร์ พร้อมจำนวนออเดอร์และคำขอรอรีเซ็ต
def list_members(admin_id,query=''):
    conn=get_connection()
    try:
        require_admin(conn,admin_id)
        query=query.strip().lower()
        return conn.execute("""SELECT u.id,u.username,u.email,COALESCE(u.contact_phone,''),u.created_at,
            (SELECT COUNT(*) FROM orders o WHERE o.user_id=u.id),
            (SELECT COUNT(*) FROM password_reset_requests r WHERE r.user_id=u.id AND r.status='pending'),u.role,u.is_blocked
            FROM users u WHERE u.role IN ('customer','admin') AND
            (?='' OR instr(lower(u.username),?)>0 OR instr(lower(u.email),?)>0 OR instr(COALESCE(u.contact_phone,''),?)>0)
            ORDER BY u.id DESC""",(query,query,query,query)).fetchall()
    finally:conn.close()

# def member_detail: อ่านข้อมูลบัญชี ที่อยู่ ออเดอร์ รายการสินค้า และประวัติคำขอรีเซ็ตของบัญชีที่เลือก
def member_detail(admin_id,user_id):
    conn=get_connection()
    try:
        require_admin(conn,admin_id)
        user=conn.execute('SELECT id,username,email,contact_phone,role,created_at FROM users WHERE id=?',(user_id,)).fetchone()
        if not user:raise ValueError('ไม่พบสมาชิก')
        address=conn.execute('SELECT shipping_name,shipping_phone,shipping_address,shipping_subdistrict,shipping_district,shipping_province,shipping_postcode FROM customer_addresses WHERE user_id=?',(user_id,)).fetchone()
        orders=conn.execute('SELECT id,order_date,total_price,order_status,payment_status FROM orders WHERE user_id=? ORDER BY id DESC',(user_id,)).fetchall()
        requests=conn.execute('SELECT id,created_at,status,processed_at FROM password_reset_requests WHERE user_id=? ORDER BY id DESC',(user_id,)).fetchall()
        items={o[0]:conn.execute("SELECT p.name,COALESCE(i.size_label,''),i.quantity,i.price FROM order_items i JOIN products p ON p.id=i.product_id WHERE i.order_id=? ORDER BY i.id",(o[0],)).fetchall() for o in orders}
        return user,address,orders,requests,items
    finally:conn.close()

# def set_member_role: ตรวจสิทธิ์และเปลี่ยนบทบาทใน transaction ป้องกันลดสิทธิ์ตนเองและ Admin คนสุดท้าย
def set_member_role(admin_id,user_id,role):
    if role not in ('admin','customer'):raise ValueError('บทบาทไม่ถูกต้อง')
    conn=get_connection()
    try:
        conn.execute('BEGIN IMMEDIATE');require_admin(conn,admin_id)
        user=conn.execute('SELECT role FROM users WHERE id=?',(user_id,)).fetchone()
        if not user:raise ValueError('ไม่พบสมาชิก')
        if role=='admin' and conn.execute('SELECT is_blocked FROM users WHERE id=?',(user_id,)).fetchone()[0]:
            raise ValueError('กรุณาปลดบล็อกก่อนมอบสิทธิ์ Admin')
        if user[0]==role:conn.rollback();return False
        if role=='customer' and user[0]=='admin':
            if conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]<=1:
                raise ValueError('ไม่สามารถลดสิทธิ์ Admin คนสุดท้ายได้')
            if user_id==admin_id:raise ValueError('ไม่สามารถลดสิทธิ์บัญชี Admin ที่กำลังใช้งานได้')
        conn.execute('UPDATE users SET role=? WHERE id=?',(role,user_id));conn.commit();return True
    except Exception:
        conn.rollback();raise
    finally:conn.close()


def require_active_customer(conn, user_id):
    """ตรวจซ้ำภายใน transaction ก่อนสร้างคำสั่งซื้อ ปิดช่องแข่งกับการบล็อก"""
    row=conn.execute('SELECT is_blocked FROM users WHERE id=?',(user_id,)).fetchone()
    if not row or row[0]:
        raise ValueError('บัญชีถูกระงับการใช้งาน กรุณาติดต่อร้านค้า')


def set_member_block(admin_id, user_id, blocked, reason):
    reason=str(reason).strip()
    if not reason or len(reason)>500:raise ValueError('กรุณาระบุเหตุผล 1–500 ตัวอักษร')
    conn=get_connection()
    try:
        conn.execute('BEGIN IMMEDIATE');require_admin(conn,admin_id)
        row=conn.execute('SELECT role,is_blocked FROM users WHERE id=?',(user_id,)).fetchone()
        if not row:raise ValueError('ไม่พบสมาชิก')
        if user_id==admin_id or row[0]!='customer':raise ValueError('บล็อกได้เฉพาะบัญชีลูกค้า')
        if bool(row[1])==bool(blocked):conn.rollback();return False
        conn.execute("""UPDATE users SET is_blocked=?,block_reason=?,
            blocked_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END,
            blocked_by=CASE WHEN ? THEN ? ELSE NULL END WHERE id=?""",
            (int(bool(blocked)),reason if blocked else None,int(bool(blocked)),int(bool(blocked)),admin_id,user_id))
        conn.execute('INSERT INTO member_block_events(user_id,admin_id,action,reason) VALUES(?,?,?,?)',
            (user_id,admin_id,'block' if blocked else 'unblock',reason))
        conn.commit();return True
    except Exception:conn.rollback();raise
    finally:conn.close()


def block_history(admin_id,user_id):
    conn=get_connection()
    try:
        require_admin(conn,admin_id)
        return conn.execute("""SELECT e.created_at,u.username,e.action,e.reason
            FROM member_block_events e JOIN users u ON u.id=e.admin_id
            WHERE e.user_id=? ORDER BY e.id DESC""",(user_id,)).fetchall()
    finally:conn.close()
