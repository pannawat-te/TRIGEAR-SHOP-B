# ไฟล์นี้: คำนวณยอดเงินและ VAT 7% ด้วย Decimal ใช้ร่วมกันทุกหน้าสำหรับ Order ใหม่
from decimal import Decimal,ROUND_HALF_UP
VAT_RATE=Decimal('7')

# def amount: ปัดจำนวนเงินสองตำแหน่ง
def amount(value):return Decimal(str(value)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)

# def totals: รวมยอดรายการก่อนภาษี แล้วคิด VAT หนึ่งครั้งจากยอดรวม
def totals(lines):
    subtotal=sum((amount(price)*qty for price,qty in lines),Decimal('0.00'))
    vat=amount(subtotal*VAT_RATE/100)
    return subtotal,vat,subtotal+vat
