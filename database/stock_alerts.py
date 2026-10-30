# ไฟล์นี้: อ่านสินค้าหรือไซซ์ที่คงเหลือ 0-3 ชิ้นจากข้อมูลจริง
from database.database import get_connection
LOW_STOCK_THRESHOLD=3

# def stock_status: แยกสินค้าใกล้หมดออกจากสินค้าหมด
def stock_status(stock):
    return 'สินค้าหมด' if stock<=0 else 'ใกล้หมด' if stock<=LOW_STOCK_THRESHOLD else 'พร้อมขาย'

# def low_stock_rows: สินค้าไม่มีไซซ์ตรวจยอดรวม สินค้ามีไซซ์ตรวจแต่ละไซซ์ ไม่ซ้ำยอดรวม
# แต่ละรายการคืน product_id, name, size, stock, status
def low_stock_rows():
    conn=get_connection()
    try:
        rows=conn.execute("""SELECT p.id,p.name,'' AS size,p.stock FROM products p
            WHERE p.stock<=? AND (p.size_type='none' OR NOT EXISTS
                (SELECT 1 FROM product_variants v WHERE v.product_id=p.id))
            UNION ALL
            SELECT p.id,p.name,v.size,v.stock FROM product_variants v
            JOIN products p ON p.id=v.product_id WHERE p.size_type!='none' AND v.stock<=?
            ORDER BY 4,2,3""",(LOW_STOCK_THRESHOLD,LOW_STOCK_THRESHOLD)).fetchall()
        return [(*row,stock_status(row[3])) for row in rows]
    finally:conn.close()
