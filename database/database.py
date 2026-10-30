# ไฟล์นี้: เชื่อมต่อ SQLite สร้าง/ปรับตาราง และเตรียมข้อมูลเริ่มต้น
import sqlite3
from pathlib import Path
import hashlib

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shop.db"


# def get_connection: เปิด SQLite ตาม DB_PATH และเปิดการตรวจความสัมพันธ์ foreign key; ผู้เรียกต้องปิด connection
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# def hash_password: แปลงรหัสผ่านเป็นค่าแฮช PBKDF2 สำหรับบันทึก แทนการเก็บรหัสที่อ่านได้
def hash_password(password):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        b"triathlon_shop_salt",
        120_000
    ).hex()


# def verify_password: แฮชรหัสที่กรอก แล้วเปรียบเทียบกับแฮชที่เก็บไว้ คืน True เมื่อถูกต้อง
def verify_password(password, stored_hash):
    return hash_password(password) == stored_hash


# def create_tables: สร้างตารางที่ยังไม่มี และเพิ่มคอลัมน์ใหม่ให้ฐานข้อมูลเดิมโดยไม่ลบข้อมูล
def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS customer_addresses (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        shipping_name TEXT NOT NULL, shipping_phone TEXT NOT NULL,
        shipping_address TEXT NOT NULL, shipping_subdistrict TEXT NOT NULL,
        shipping_district TEXT NOT NULL, shipping_province TEXT NOT NULL,
        shipping_postcode TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS password_reset_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        processed_at TEXT,
        processed_by INTEGER REFERENCES users(id)
    );
    CREATE UNIQUE INDEX IF NOT EXISTS one_pending_password_reset
        ON password_reset_requests(user_id) WHERE status='pending';

    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand_id INTEGER,
        price REAL NOT NULL DEFAULT 0,
        stock INTEGER NOT NULL DEFAULT 0,
        description TEXT,
        image TEXT,
        is_featured INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        image_path TEXT NOT NULL,
        sort_order INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS product_categories (
        product_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (product_id, category_id),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price REAL NOT NULL DEFAULT 0,
        order_status TEXT NOT NULL DEFAULT 'กำลังตรวจสอบ',
        payment_status TEXT NOT NULL DEFAULT 'ยังไม่ชำระ',
        order_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        slip TEXT,
        payment_status TEXT NOT NULL DEFAULT 'ยังไม่ชำระ',
        payment_date TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS refunds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        refund_status TEXT NOT NULL DEFAULT 'ร้านค้ากำลังเตรียมการคืนเงิน',
        refund_date TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        size TEXT NOT NULL, stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
        UNIQUE(product_id,size))""")
    cols={x[1] for x in cur.execute("PRAGMA table_info(products)")}
    if 'size_type' not in cols:
        cur.execute("ALTER TABLE products ADD COLUMN size_type TEXT NOT NULL DEFAULT 'none'")
    cols={x[1] for x in cur.execute("PRAGMA table_info(order_items)")}
    if 'variant_id' not in cols:
        cur.execute("ALTER TABLE order_items ADD COLUMN variant_id INTEGER")
    if 'size_label' not in cols:
        cur.execute("ALTER TABLE order_items ADD COLUMN size_label TEXT")
    for table, additions in {
        "orders": {"refund_bank":"TEXT", "refund_account_name":"TEXT", "refund_account_number":"TEXT", "shipping_name":"TEXT", "shipping_phone":"TEXT", "shipping_address":"TEXT", "shipping_subdistrict":"TEXT", "shipping_district":"TEXT", "shipping_province":"TEXT", "shipping_postcode":"TEXT"},
        "refunds": {"slip":"TEXT", "stock_restored":"INTEGER NOT NULL DEFAULT 0"}
    }.items():
        existing={r[1] for r in cur.execute(f"PRAGMA table_info({table})")}
        for name, definition in additions.items():
            if name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    # ตะกร้าถาวร variant_key=0 สำหรับสินค้าที่ไม่มีไซซ์ เพื่อให้ primary key ไม่รับ NULL
    cur.execute("""CREATE TABLE IF NOT EXISTS cart_items (
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        variant_key INTEGER NOT NULL DEFAULT 0,
        quantity INTEGER NOT NULL CHECK(quantity>0),
        selected INTEGER NOT NULL DEFAULT 1 CHECK(selected IN (0,1)),
        PRIMARY KEY(user_id,product_id,variant_key)
    )""")
    # ภาพตารางไซซ์เฉพาะสินค้า NULL หมายถึงใช้ภาพอัตโนมัติตามประเภท
    product_cols={r[1] for r in cur.execute("PRAGMA table_info(products)")}
    if 'size_chart' not in product_cols:cur.execute("ALTER TABLE products ADD COLUMN size_chart TEXT")
    # Order เก่าไม่มี snapshot VAT จึงไม่บวกย้อนหลัง
    order_cols={r[1] for r in cur.execute("PRAGMA table_info(orders)")}
    for name,definition in {"subtotal":"NUMERIC","vat_rate":"NUMERIC NOT NULL DEFAULT 0","vat_amount":"NUMERIC NOT NULL DEFAULT 0"}.items():
        if name not in order_cols:cur.execute(f"ALTER TABLE orders ADD COLUMN {name} {definition}")
    # บัญชีรับเงินคืนเริ่มต้นแยกตามผู้ใช้ ไม่เปลี่ยนบัญชีใน Order เก่า
    cur.execute("""CREATE TABLE IF NOT EXISTS customer_refund_accounts (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        refund_bank TEXT NOT NULL,
        refund_account_name TEXT NOT NULL,
        refund_account_number TEXT NOT NULL
    )""")
    # ใบเสร็จหนึ่งรายการต่อ Order เก็บ snapshot ไม่เปลี่ยนตามสินค้าในอนาคต
    cur.execute("""CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id),
        receipt_number TEXT UNIQUE,
        issued_at TEXT NOT NULL,
        snapshot_json TEXT NOT NULL
    )""")
    user_cols={r[1] for r in cur.execute("PRAGMA table_info(users)")}
    if 'profile_image' not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
    if 'contact_phone' not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN contact_phone TEXT")
    if 'must_change_password' not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
    if 'temporary_password_expires' not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN temporary_password_expires TEXT")
    for name, definition in {
        'is_blocked': 'INTEGER NOT NULL DEFAULT 0',
        'block_reason': 'TEXT', 'blocked_at': 'TEXT', 'blocked_by': 'INTEGER'
    }.items():
        if name not in user_cols:
            cur.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
    cur.execute("""CREATE TABLE IF NOT EXISTS member_block_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        admin_id INTEGER NOT NULL REFERENCES users(id),
        action TEXT NOT NULL CHECK(action IN ('block','unblock')),
        reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_refund_per_order ON refunds(order_id)")
    # แก้รายการเก่าที่ถูกยกเลิกขณะรอตรวจสลิป ให้ Admin คืนเงินต่อได้
    # รายการเหล่านี้ยังไม่ถูกตัด Stock จึงไม่เพิ่ม Stock ในการย้ายสถานะ
    cur.execute("""INSERT OR IGNORE INTO refunds(order_id,amount,refund_status,stock_restored)
        SELECT o.id,o.total_price,'รอคืนเงิน',0 FROM orders o
        WHERE o.order_status='ยกเลิกแล้ว' AND EXISTS
        (SELECT 1 FROM payments p WHERE p.order_id=o.id AND COALESCE(p.slip,'')!='')""")
    cur.execute("""UPDATE orders SET order_status='สถานะถูกยกเลิก - รอคืนเงิน'
        WHERE order_status='ยกเลิกแล้ว' AND EXISTS
        (SELECT 1 FROM refunds r WHERE r.order_id=orders.id AND r.refund_status='รอคืนเงิน')""")
    from database.email_otp import create_schema
    create_schema(conn)
    conn.commit()
    conn.close()


# def seed_data: เพิ่มแบรนด์ หมวดหมู่ และบัญชี Admin เริ่มต้น โดยไม่เติมสินค้า
def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    brands = ["Nike", "adidas", "ASICS", "HOKA", "Garmin", "Speedo", "Arena", "อื่น ๆ"]
    for name in brands:
        cur.execute("INSERT OR IGNORE INTO brands(name) VALUES(?)", (name,))

    mains = ["จักรยาน", "รองเท้าวิ่ง", "ว่ายน้ำ", "อุปกรณ์เสริม"]
    for name in mains:
        cur.execute("SELECT id FROM categories WHERE TRIM(name)=? AND parent_id IS NULL", (name,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO categories(name,parent_id) VALUES(?,NULL)", (name,))

    cur.execute("SELECT id, name FROM categories WHERE parent_id IS NULL")
    main_map = {name: cid for cid, name in cur.fetchall()}

    subs = {
        "จักรยาน": ["จักรยาน", "รองเท้าและคลีทจักรยาน", "อะไหล่และอุปกรณ์จักรยาน"],
        "รองเท้าวิ่ง": ["รองเท้าวิ่ง", "อุปกรณ์วิ่ง"],
        "ว่ายน้ำ": ["ชุดว่ายน้ำ", "อุปกรณ์ว่ายน้ำ"],
        "อุปกรณ์เสริม": ["Energy Gel", "Protein / Whey", "Energy Bar", "อุปกรณ์เสริมอื่น ๆ"],
    }
    for parent, children in subs.items():
        for child in children:
            cur.execute(
                "SELECT id FROM categories WHERE name=? AND parent_id=?",
                (child, main_map[parent])
            )
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO categories(name, parent_id) VALUES(?, ?)",
                    (child, main_map[parent])
                )

    cur.execute("SELECT id FROM users WHERE username='admin'")
    if cur.fetchone() is None:
        cur.execute(
            """INSERT INTO users(username,email,password,role)
               VALUES(?,?,?,?)""",
            ("admin", "admin@triathlonshop.com", hash_password("Admin123"), "admin")
        )

    # ไม่เติมสินค้าตัวอย่างอัตโนมัติ ร้านว่างอาจเกิดจาก Admin ตั้งใจลบสินค้า
    conn.commit()
    conn.close()


# def merge_duplicate_categories: รวมหมวดหมู่ชื่อซ้ำระดับเดียวกัน โดยย้ายการเชื่อมโยงสินค้าและหมวดย่อย
def merge_duplicate_categories():
    """Merge same-name siblings, retaining all product links and descendants."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("UPDATE categories SET name=TRIM(name)")
        while True:
            groups = conn.execute("SELECT name,parent_id,MIN(id) FROM categories GROUP BY name,parent_id HAVING COUNT(*)>1").fetchall()
            if not groups:
                break
            for name, parent, keep in groups:
                duplicates = conn.execute("SELECT id FROM categories WHERE name=? AND parent_id IS ? AND id<>?", (name,parent,keep)).fetchall()
                for (old,) in duplicates:
                    conn.execute("INSERT OR IGNORE INTO product_categories(product_id,category_id) SELECT product_id,? FROM product_categories WHERE category_id=?", (keep,old))
                    conn.execute("UPDATE categories SET parent_id=? WHERE parent_id=?", (keep,old))
                    conn.execute("DELETE FROM product_categories WHERE category_id=?", (old,))
                    conn.execute("DELETE FROM categories WHERE id=?", (old,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# def initialize_database: เตรียมตาราง รวมหมวดซ้ำ และเพิ่มข้อมูลเริ่มต้นก่อนเปิดโปรแกรม
def initialize_database():
    create_tables()
    merge_duplicate_categories()
    seed_data()
    # การเปิดโปรแกรมเตรียมเฉพาะโครงสร้างและข้อมูลระบบ ไม่สร้างสินค้า
