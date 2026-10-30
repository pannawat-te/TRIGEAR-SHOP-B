TRI GEAR V25 — จัดการ์ดสินค้า ดูสลิป และ Popup รายการคำสั่งซื้อ
รวมฟีเจอร์ V24 และแก้คืนเงิน V23
ไฟล์ที่แก้จาก V24: ui/customer_home.py, ui/orders.py, ui/checkout.py
ไฟล์ใหม่: ui/order_previews.py
ภาพและชื่อสินค้ามีพื้นที่เท่ากัน ชื่อแสดงครบโดยขยายความสูงร่วมกันเมื่อยาวเกินสองบรรทัด
ดูสลิปใน Checkout หน้าสรุป และแต่ละ Order
รายการสินค้า Order เปิด Popup ที่มี Scrollbar
ผ่าน Syntax ทดสอบอ่านข้อมูล ตรวจเจ้าของ Order และกรณีไม่พบสลิป
ยังไม่ได้ทดสอบ GUI บน Windows
สำรอง database/shop.db และ uploads ก่อนอัปเดต
