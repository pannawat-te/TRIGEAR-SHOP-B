# ไฟล์นี้: เพิ่มข้อมูลสินค้าสาธิตพร้อมรูปภาพสำหรับทดลองร้าน
"""Optional catalog of generic demonstration products; never replaces existing products."""
CATALOG = [
 ('หมวกกันน็อกจักรยาน','จักรยาน','อะไหล่และอุปกรณ์จักรยาน',1290,'none',[], 'หมวกจักรยานระบายอากาศ พร้อมสายรัดปรับกระชับ เหมาะสำหรับการปั่นประจำวัน'),
 ('รองเท้าจักรยานระบบคลีท','จักรยาน','รองเท้าและคลีทจักรยาน',2490,'shoe_cm',[('25.0',3),('25.5',3),('26.0',3),('26.5',3)], 'รองเท้าจักรยานพื้นแข็งสำหรับใช้กับระบบคลีท ตรวจสอบความเข้ากันได้กับบันไดและคลีทก่อนใช้งาน'),
 ('กระติกน้ำจักรยาน 750 มล.','จักรยาน','อะไหล่และอุปกรณ์จักรยาน',290,'none',[], 'กระติกน้ำบีบได้สำหรับพกติดจักรยาน ความจุสาธิต 750 มล. ใช้เติมน้ำระหว่างปั่น'),
 ('รองเท้าวิ่งฝึกซ้อม Road','รองเท้าวิ่ง','รองเท้าวิ่ง',1990,'shoe_cm',[('25.0',3),('25.5',3),('26.0',3),('26.5',3)], 'รองเท้าวิ่งถนนสำหรับการฝึกซ้อมประจำวัน เลือกขนาดตามความยาวเท้าและทดลองความกระชับ'),
 ('รองเท้าวิ่งเทรล Trail','รองเท้าวิ่ง','รองเท้าวิ่ง',2290,'shoe_cm',[('25.0',3),('25.5',3),('26.0',3),('26.5',3)], 'รองเท้าวิ่งพื้นดอกยางสำหรับเส้นทางธรรมชาติ เหมาะสำหรับการฝึกซ้อมบนพื้นผิวไม่เรียบ'),
 ('รองเท้าวิ่งน้ำหนักเบา Racing','รองเท้าวิ่ง','รองเท้าวิ่ง',2690,'shoe_cm',[('25.0',3),('25.5',3),('26.0',3),('26.5',3)], 'รองเท้าวิ่งน้ำหนักเบาสำหรับการฝึกทำความเร็ว เลือกไซซ์ที่กระชับและไม่บีบปลายเท้า'),
 ('แว่นตาว่ายน้ำ Training','ว่ายน้ำ','อุปกรณ์ว่ายน้ำ',590,'none',[], 'แว่นตาว่ายน้ำพร้อมสายรัดปรับได้ สำหรับฝึกในสระ ตรวจสอบความกระชับรอบดวงตาก่อนใช้งาน'),
 ('หมวกว่ายน้ำซิลิโคน','ว่ายน้ำ','อุปกรณ์ว่ายน้ำ',250,'none',[], 'หมวกว่ายน้ำซิลิโคนยืดหยุ่น ช่วยเก็บเส้นผมระหว่างว่ายน้ำ ล้างและผึ่งให้แห้งหลังใช้งาน'),
 ('กางเกงว่ายน้ำ Jammer','ว่ายน้ำ','ชุดว่ายน้ำ',890,'clothing',[('S',3),('M',3),('L',3),('XL',3)], 'กางเกงว่ายน้ำทรง Jammer สำหรับฝึกในสระ เลือกไซซ์ตามความกระชับที่ต้องการ'),
 ('เจลพลังงานสำหรับกีฬา','อุปกรณ์เสริม','Energy Gel',65,'none',[], 'ตัวอย่างเจลพลังงานแบบซองสำหรับพกพา ข้อมูลส่วนประกอบและโภชนาการต้องใช้ฉลากสินค้าจริงก่อนจำหน่าย'),
 ('เวย์โปรตีนสำหรับนักกีฬา','อุปกรณ์เสริม','Protein / Whey',990,'none',[], 'ตัวอย่างผลิตภัณฑ์เวย์โปรตีนบรรจุกระปุก ตรวจสอบส่วนประกอบ สารก่อภูมิแพ้ และวิธีใช้จากฉลากสินค้าจริง'),
 ('บาร์พลังงานสำหรับกีฬา','อุปกรณ์เสริม','Energy Bar',55,'none',[], 'ตัวอย่างบาร์พลังงานบรรจุซองสำหรับพกพา ตรวจสอบส่วนประกอบและสารก่อภูมิแพ้จากฉลากสินค้าจริง'),
]


# def add_sample_catalog: เพิ่มสินค้าสาธิตและภาพลง connection ที่รับมา โดยผู้เรียกจัดการ commit
def add_sample_catalog(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS sample_catalog_imports (sample_key TEXT PRIMARY KEY)")
    for index,(name,parent,category,price,kind,variants,description) in enumerate(CATALOG):
        key=f'trigear_sample_{index+1:02d}'
        if conn.execute('SELECT 1 FROM sample_catalog_imports WHERE sample_key=?',(key,)).fetchone():continue
        if conn.execute('SELECT 1 FROM products WHERE name=?',(name,)).fetchone():
            conn.execute('INSERT INTO sample_catalog_imports(sample_key) VALUES(?)',(key,));continue
        parent_id=conn.execute('SELECT id FROM categories WHERE name=? AND parent_id IS NULL ORDER BY id LIMIT 1',(parent,)).fetchone()[0]
        row=conn.execute('SELECT id FROM categories WHERE name=? AND parent_id=? ORDER BY id LIMIT 1',(category,parent_id)).fetchone()
        if row:category_id=row[0]
        else:category_id=conn.execute('INSERT INTO categories(name,parent_id) VALUES(?,?)',(category,parent_id)).lastrowid
        brand=conn.execute("SELECT id FROM brands WHERE name='อื่น ๆ'").fetchone()[0]
        stock=sum(v[1] for v in variants) if variants else 12
        image=f'assets/sample_products/product_{index+1:02d}.png'
        pid=conn.execute('INSERT INTO products(name,brand_id,price,stock,description,image,is_featured,size_type) VALUES(?,?,?,?,?,?,0,?)',(name,brand,price,stock,description+'\n\nสินค้าตัวอย่างสำหรับสาธิตระบบ: ภาพสร้างขึ้น ราคาและ Stock เป็นข้อมูลสมมติ',image,kind)).lastrowid
        conn.execute('INSERT INTO product_categories(product_id,category_id) VALUES(?,?)',(pid,category_id))
        conn.execute('INSERT INTO sample_catalog_imports(sample_key) VALUES(?)',(key,))
        for size,amount in variants:conn.execute('INSERT INTO product_variants(product_id,size,stock) VALUES(?,?,?)',(pid,size,amount))
