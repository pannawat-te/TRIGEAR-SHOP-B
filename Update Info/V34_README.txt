TRIGEAR V34 — UI ตะกร้า/Checkout และ VAT เพิ่ม 7%
ตะกร้า: รายการด้านซ้าย สรุปก่อน VAT ภาษี ยอดรวม และปุ่มด้านขวา
Checkout: QR/สลิปด้านซ้าย รายการ/ยอดรวมด้านขวาบน ที่อยู่/บัญชีคืนเงินเลื่อนด้านขวาล่าง
คิด VAT 7% จากยอดรวมสินค้าก่อนภาษีด้วย Decimal ปัดสองตำแหน่ง
หน้าสรุปก่อนยืนยันและใบเสร็จแสดงก่อน VAT ภาษี และรวม
ประวัติ Order/Admin/ยอดชำระ/ยอดคืนเงินใช้ total_price ที่รวม VAT แล้ว
Order เก่าคงยอดเดิม ไม่บวกภาษีย้อนหลัง
ฐานข้อมูลเพิ่ม orders.subtotal, vat_rate, vat_amount โดยไม่แก้ยอดเก่า
ใบเสร็จเก่าที่ snapshot แล้วคงเดิม
ไฟล์ใหม่ services/pricing.py
ไฟล์แก้ ui/cart.py, ui/checkout.py, services/receipt.py, database/database.py
รวม V33 ทั้งหมด
ผ่าน Syntax และทดสอบการสร้าง Order/ยอดชำระ/VAT/ปัดเศษ/คืนเงิน/Order เก่า และตรวจภาพ PDF
ยังไม่ได้ทดสอบ GUI Windows
สำรอง database/shop.db และ uploads ก่อนอัปเดต ห้ามทับข้อมูลจริงด้วยข้อมูลตัวอย่าง
