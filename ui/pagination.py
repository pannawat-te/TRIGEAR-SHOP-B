# ไฟล์นี้: แบ่งสินค้าเป็นหน้าละ 9 รายการ ใช้ร่วมกับผลค้นหาและหมวดหมู่
PAGE_SIZE=9

# def page_items: คืนรายการในหน้า เลขหน้าที่ถูกต้อง และจำนวนหน้าทั้งหมด
def page_items(items,page=1):
    pages=max(1,(len(items)+PAGE_SIZE-1)//PAGE_SIZE);page=max(1,min(page,pages))
    return items[(page-1)*PAGE_SIZE:page*PAGE_SIZE],page,pages
