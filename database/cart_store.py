# ไฟล์นี้: เก็บตะกร้าถาวรแยกตาม user_id สินค้า ไซซ์ จำนวน และช่องติ๊ก
from database.database import get_connection

# def load_cart: อ่านตะกร้าผู้ใช้และข้ามสินค้า/ไซซ์ที่ถูกลบแล้ว
def load_cart(user_id):
    conn=get_connection()
    try:
        rows=conn.execute("""SELECT c.product_id,c.variant_key,c.quantity,c.selected
            FROM cart_items c JOIN products p ON p.id=c.product_id
            WHERE c.user_id=? AND (c.variant_key=0 OR EXISTS
            (SELECT 1 FROM product_variants v WHERE v.id=c.variant_key AND v.product_id=c.product_id))""",(user_id,)).fetchall()
        cart={(pid,vid or None):qty for pid,vid,qty,selected in rows}
        unchecked={(pid,vid or None) for pid,vid,qty,selected in rows if not selected}
        return cart,unchecked
    finally:conn.close()

# def save_cart: บันทึกตะกร้าทั้งชุดของบัญชีเดียวใน transaction ไม่กระทบผู้ใช้คนอื่น
def save_cart(user_id,cart,unchecked):
    conn=get_connection()
    try:
        with conn:
            conn.execute('DELETE FROM cart_items WHERE user_id=?',(user_id,))
            for key,quantity in cart.items():
                pid,vid=key if isinstance(key,tuple) else (key,None)
                if type(quantity) is not int or quantity<1:raise ValueError('จำนวนสินค้าไม่ถูกต้อง')
                conn.execute('INSERT INTO cart_items(user_id,product_id,variant_key,quantity,selected) VALUES(?,?,?,?,?)',(user_id,pid,vid or 0,quantity,int(key not in unchecked)))
    finally:conn.close()

# def remove_purchased: ลบเฉพาะรายการที่ซื้อใน transaction เดียวกับ Order
# หากตะกร้าถูกเปลี่ยนโดยโปรแกรมอีกหน้าต่าง ให้หยุดและ rollback Order แทนการลบผิดรายการ
def remove_purchased(conn,user_id,purchased):
    for key,quantity in purchased.items():
        pid,vid=key if isinstance(key,tuple) else (key,None)
        result=conn.execute('DELETE FROM cart_items WHERE user_id=? AND product_id=? AND variant_key=? AND quantity=?',(user_id,pid,vid or 0,quantity))
        if result.rowcount!=1:raise ValueError('ตะกร้ามีการเปลี่ยนแปลง กรุณากลับไปตรวจสอบก่อนสั่งซื้อใหม่')
