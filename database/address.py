# ไฟล์นี้: ตรวจสอบ อ่าน และบันทึกที่อยู่จัดส่งเริ่มต้นของแต่ละบัญชี
"""One editable default shipping address per customer."""
import re
from database.database import get_connection

ADDRESS_FIELDS = (
    ("shipping_name", "ชื่อ–นามสกุลผู้รับ"),
    ("shipping_phone", "เบอร์โทรศัพท์"),
    ("shipping_address", "บ้านเลขที่ / หมู่ / ถนน"),
    ("shipping_subdistrict", "ตำบล / แขวง"),
    ("shipping_district", "อำเภอ / เขต"),
    ("shipping_province", "จังหวัด"),
    ("shipping_postcode", "รหัสไปรษณีย์"),
)

# def validate_address: ตรวจข้อมูลที่อยู่ครบ เบอร์โทร และรหัสไปรษณีย์; คืนข้อมูลที่จัดรูปแบบแล้วหรือแจ้ง ValueError
def validate_address(values):
    address = {key: values.get(key, "").strip() for key, _ in ADDRESS_FIELDS}
    if any(not value for value in address.values()):
        raise ValueError("กรุณากรอกข้อมูลผู้รับและที่อยู่จัดส่งให้ครบทุกช่อง")
    address["shipping_phone"] = re.sub(r"[\s-]", "", address["shipping_phone"])
    if not re.fullmatch(r"0[0-9]{8,9}", address["shipping_phone"]):
        raise ValueError("กรุณากรอกเบอร์โทรศัพท์ไทย 9–10 หลัก เริ่มด้วย 0")
    if not re.fullmatch(r"[0-9]{5}", address["shipping_postcode"]):
        raise ValueError("กรุณากรอกรหัสไปรษณีย์ 5 หลัก")
    return address

# def get_address: อ่านที่อยู่ตาม user_id; คืน dict ว่างเมื่อบัญชียังไม่บันทึกที่อยู่
def get_address(user_id):
    conn = get_connection()
    try:
        keys = [key for key, _ in ADDRESS_FIELDS]
        row = conn.execute("SELECT " + ",".join(keys) + " FROM customer_addresses WHERE user_id=?", (user_id,)).fetchone()
        return dict(zip(keys, row)) if row else {}
    finally:
        conn.close()

# def save_address: ตรวจที่อยู่แล้วเพิ่มหรือปรับรายการของบัญชีเดิมในธุรกรรมเดียว
def save_address(user_id, values):
    address = validate_address(values)
    keys = list(address)
    conn = get_connection()
    try:
        with conn:
            conn.execute("INSERT INTO customer_addresses (user_id," + ",".join(keys) + ") VALUES (" + ",".join("?" for _ in range(8)) + ") ON CONFLICT(user_id) DO UPDATE SET " + ",".join(key + "=excluded." + key for key in keys), (user_id, *address.values()))
    finally:
        conn.close()
