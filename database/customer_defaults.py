# ไฟล์นี้: ข้อมูลเริ่มต้นสำหรับ Checkout บันทึกแยกจากข้อมูลในคำสั่งซื้อเดิม
import re
from database.database import get_connection
from database.address import validate_address
REFUND_FIELDS=(('refund_bank','ธนาคาร'),('refund_account_name','ชื่อเจ้าของบัญชี'),('refund_account_number','เลขบัญชี'))

# def validate_refund: ตรวจบัญชีรับเงินคืนและจัดรูปแบบเลขบัญชี
def validate_refund(values):
    data={key:str(values.get(key) or '').strip() for key,_ in REFUND_FIELDS}
    data['refund_account_number']=re.sub(r'[\s-]','',data['refund_account_number'])
    if not data['refund_bank'] or not data['refund_account_name'] or not re.fullmatch(r'[0-9]{9,15}',data['refund_account_number']):
        raise ValueError('กรุณากรอกธนาคาร ชื่อเจ้าของบัญชี และเลขบัญชี 9–15 หลัก')
    return data

# def get_refund: อ่านเฉพาะบัญชีรับเงินคืนของผู้ใช้ปัจจุบัน
def get_refund(user_id):
    conn=get_connection()
    try:
        row=conn.execute('SELECT refund_bank,refund_account_name,refund_account_number FROM customer_refund_accounts WHERE user_id=?',(user_id,)).fetchone()
        return dict(zip([key for key,_ in REFUND_FIELDS],row)) if row else {}
    finally:conn.close()

# def write_refund: เขียนบัญชีใน transaction ของผู้เรียก ไม่ commit แยกจากคำสั่งซื้อ
def write_refund(conn,user_id,values,overwrite=True):
    data=validate_refund(values)
    action='DO UPDATE SET '+','.join(key+'=excluded.'+key for key in data) if overwrite else 'DO NOTHING'
    conn.execute('INSERT INTO customer_refund_accounts(user_id,refund_bank,refund_account_name,refund_account_number) VALUES(?,?,?,?) ON CONFLICT(user_id) '+action,(user_id,*data.values()))

# def save_refund: บันทึกบัญชีรับเงินคืนจากหน้าบัญชีของฉัน
def save_refund(user_id,values):
    conn=get_connection()
    try:
        with conn:write_refund(conn,user_id,values)
    finally:conn.close()

# def save_checkout_defaults: ไม่มีข้อมูลเดิมให้บันทึกอัตโนมัติ มีแล้วเปลี่ยนเฉพาะเมื่อผู้ใช้เลือก
# ต้องเรียกใน transaction สร้าง Order เพื่อ rollback ข้อมูลเริ่มต้นด้วยเมื่อ Order ล้มเหลว
def save_checkout_defaults(conn,user_id,shipping,refund,overwrite=False):
    data=validate_address(shipping)
    action='DO UPDATE SET '+','.join(key+'=excluded.'+key for key in data) if overwrite else 'DO NOTHING'
    conn.execute('INSERT INTO customer_addresses(user_id,'+','.join(data)+') VALUES('+','.join('?' for _ in range(8))+') ON CONFLICT(user_id) '+action,(user_id,*data.values()))
    write_refund(conn,user_id,refund,overwrite)
