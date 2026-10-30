# ไฟล์นี้: อ่าน/บันทึกรายการภาพสินค้าและลำดับภาพ
"""Multiple images per product, preserving the legacy products.image cover."""
from database.database import get_connection
from ui.image_utils import store_image

# def images_for: อ่านรูปสินค้าตามลำดับ; ใช้รูป fallback เมื่อยังไม่มีแกลเลอรี
def images_for(product_id, fallback=None):
    with get_connection() as db:
        paths = [r[0] for r in db.execute(
            "SELECT image_path FROM product_images WHERE product_id=? ORDER BY sort_order,id", (product_id,))]
    return paths or ([fallback] if fallback else [])

# def save_gallery: บันทึกรายการและลำดับรูป พร้อมปรับรูปหลักของสินค้า
def save_gallery(db, product_id, paths):
    """Caller owns transaction; paths already copied into uploads/products."""
    db.execute("DELETE FROM product_images WHERE product_id=?", (product_id,))
    db.executemany("INSERT INTO product_images(product_id,image_path,sort_order) VALUES(?,?,?)",
                   [(product_id, path, i) for i,path in enumerate(paths)])
    db.execute("UPDATE products SET image=? WHERE id=?", (paths[0] if paths else '', product_id))
