# ไฟล์นี้: กฎรหัสผ่านใหม่ร่วมกัน รับเฉพาะ A-Z a-z 0-9
import re
PASSWORD_HINT='รหัสผ่านอย่างน้อย 8 ตัว มีตัวพิมพ์ใหญ่และตัวเลข ใช้เฉพาะ A-Z, a-z, 0-9'

# def allowed_characters: อนุญาตค่าว่างขณะลบข้อความ แต่ไม่รับช่องว่างหรือสัญลักษณ์
def allowed_characters(value):return re.fullmatch(r'[A-Za-z0-9]*',value) is not None

# def valid_password: ตรวจความยาว ตัวพิมพ์ใหญ่ ตัวเลข และชนิดอักขระก่อนบันทึก
def valid_password(value):
    return len(value)>=8 and allowed_characters(value) and re.search(r'[A-Z]',value) is not None and re.search(r'[0-9]',value) is not None
