TRIGEAR V35 — กลับตะกร้า ขยาย QR และกำหนด Role
Checkout กลับตะกร้าเดิม ไม่กลับ main และไม่ล้างสินค้า
เพิ่มปุ่มขยาย QR Payment
Admin จัดการสมาชิกแสดงทั้ง Admin/Customer และคอลัมน์ Role
ปุ่มตั้งเป็น Admin / Customer มีข้อความยืนยันบัญชี
ตรวจสิทธิ์ผู้สั่งเปลี่ยน Role ป้องกันลดสิทธิ์ตนเองและ Admin คนสุดท้าย
เมนูบทบาทใหม่ใช้เมื่อเข้าสู่ระบบครั้งถัดไป
ไฟล์แก้จาก V34: ui/checkout.py, ui/admin/members.py, database/members.py
รวม V34 ทั้งหมด
ผ่าน Syntax และทดสอบนำทาง/คงตะกร้า/QR/เปลี่ยน Role/ตรวจสิทธิ์/กัน Admin คนสุดท้าย
ยังไม่ได้ทดสอบ GUI Windows
สำรอง database/shop.db และ uploads ก่อนอัปเดต ห้ามทับข้อมูลจริงด้วยข้อมูลตัวอย่าง
