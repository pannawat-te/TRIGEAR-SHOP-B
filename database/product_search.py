# ไฟล์นี้: ค้นหาสินค้าตามชื่อ/แบรนด์และ Category รวมหมวดย่อย โดยไม่แสดงสินค้าซ้ำ
from database.database import get_connection

# def search_products: คืนรายการสินค้าสำหรับตาราง Admin ใช้ parameter ป้องกันคำค้นกระทบ SQL
def search_products(keyword='',category_id=None):
    query="""SELECT p.id,p.name,COALESCE(b.name,'-'),p.price,p.stock,p.is_featured
        FROM products p LEFT JOIN brands b ON p.brand_id=b.id WHERE 1=1"""
    params=[]
    keyword=keyword.strip()
    if keyword:
        # ค้นอักขระ % และ _ ตามที่พิมพ์ ไม่ตีความเป็น wildcard
        literal=keyword.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        query+=" AND (p.name LIKE ? ESCAPE '\\' OR b.name LIKE ? ESCAPE '\\')"
        params.extend(['%'+literal+'%']*2)
    if category_id is not None:
        query+=""" AND EXISTS (SELECT 1 FROM product_categories pc WHERE pc.product_id=p.id
            AND pc.category_id IN (WITH RECURSIVE descendants(id) AS
                (SELECT id FROM categories WHERE id=? UNION
                 SELECT c.id FROM categories c JOIN descendants d ON c.parent_id=d.id)
                SELECT id FROM descendants))"""
        params.append(category_id)
    conn=get_connection()
    try:return conn.execute(query+' ORDER BY p.id DESC',params).fetchall()
    finally:conn.close()
