"""ทดสอบ flow สั่งซื้อจริงกับ SQLite ชั่วคราว โดยไม่เปิดหน้าต่างหรือส่งเมล"""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database import database as db
from ui.cart import CartPage
from ui.checkout import CheckoutPage
from ui.customer_home import CustomerHome
from ui.orders import OrdersPage
from ui.pagination import page_items
from database.cart_store import load_cart

class ShopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old_db=db.DB_PATH;db.DB_PATH=Path(self.tmp.name)/'shop.db';db.create_tables()
        CartPage.carts.clear();CartPage.unchecked.clear();CartPage.loaded_users.clear()
        with db.get_connection() as c:
            c.execute("INSERT INTO users(id,username,email,password,role) VALUES(1,'customer','user@example.com','hash','customer')")
            c.executemany('INSERT INTO products(id,name,price,stock,size_type) VALUES(?,?,?,?,?)',[(i,f'product {i}',100.10,20,'none') for i in range(1,33)])
    def tearDown(self):db.DB_PATH=self.old_db;self.tmp.cleanup();CartPage.carts.clear();CartPage.unchecked.clear();CartPage.loaded_users.clear()
    def test_cart_limits_persistence(self):
        for i in range(1,31):self.assertTrue(CartPage.add_item(1,i))
        self.assertFalse(CartPage.add_item(1,31))
        self.assertTrue(CartPage.add_item(1,1,quantity=9));self.assertFalse(CartPage.add_item(1,1))
        CartPage.unchecked[1]={(2,None)};CartPage.persist(1);CartPage.load_saved(1)
        self.assertEqual(CartPage.total_quantity(1),39);self.assertEqual(sum(CartPage.selected_items(1).values()),38)
        self.assertEqual(len(CartPage.carts[1]),30)
    def test_selected_checkout_vat_defaults(self):
        self.assertTrue(CartPage.add_item(1,1,quantity=2));self.assertTrue(CartPage.add_item(1,2))
        CartPage.unchecked[1]={(2,None)};CartPage.persist(1)
        page=CheckoutPage.__new__(CheckoutPage);page.user_id=1;page.checkout_items=CartPage.selected_items(1)
        page.username='customer';page.root=Mock();page.frame=Mock();page.back_callback=Mock()
        def var(value):m=Mock();m.get.return_value=value;return m
        fields=dict(shipping_name='Test User',shipping_phone='0812345678',shipping_address='123',shipping_subdistrict='A',shipping_district='B',shipping_province='Khon Kaen',shipping_postcode='40000')
        page.shipping_fields={k:var(v) for k,v in fields.items()};page.refund_bank=var('Test Bank');page.refund_name=var('Test User');page.refund_number=var('1234567890');page.save_defaults=var(False)
        slip=Path(self.tmp.name)/'test-slip.png';slip.write_bytes(b'test fixture')
        page.slip_var=var(str(slip));page.review_items_snapshot=page.review_items()
        (Path(self.tmp.name)/'app/ui').mkdir(parents=True)
        import ui.checkout as checkout
        with patch.object(checkout,'__file__',str(Path(self.tmp.name)/'app/ui/checkout.py')),patch('ui.checkout.messagebox') as dialogs:
            page.place_order(0,confirmed=True);dialogs.showerror.assert_not_called()
        with db.get_connection() as c:
            row=c.execute('SELECT subtotal,vat_amount,total_price,payment_status FROM orders').fetchone()
            self.assertEqual(tuple(float(v) for v in row[:3]),(200.2,14.01,214.21));self.assertEqual(row[3],'รอตรวจสอบสลิป')
            self.assertEqual(c.execute('SELECT product_id,quantity FROM order_items').fetchall(),[(1,2)])
            self.assertEqual(c.execute('SELECT stock FROM products WHERE id=1').fetchone()[0],20)
            self.assertEqual(c.execute('SELECT shipping_name FROM customer_addresses WHERE user_id=1').fetchone()[0],'Test User')
        saved,unchecked=load_cart(1);self.assertEqual(saved,{(2,None):1});self.assertEqual(unchecked,{(2,None)})
        self.assertEqual(CartPage.total_quantity(1),1);page.back_callback.assert_called_once()
    def test_pagination_sorting_status(self):
        rows=[(i,'p','brand',33-i) for i in range(32)]
        ordered=CustomerHome.sorted_products(rows,'ราคา: จากน้อยไปมาก')
        a,page,pages=page_items(ordered,1);self.assertEqual(len(a),9);self.assertEqual(pages,4)
        self.assertEqual([r[3] for r in a],list(range(2,11)))
        self.assertEqual(CustomerHome.sorted_products(rows,'ค่าเริ่มต้น'),rows)
        self.assertEqual(OrdersPage.status_group('สถานะถูกยกเลิก - รอคืนเงิน'),'ยกเลิก')
        self.assertEqual(OrdersPage.status_group('จัดส่งสำเร็จ'),'สำเร็จ')
        self.assertEqual(OrdersPage.status_group('กำลังตรวจสอบ'),'รอตรวจสอบ')
    def test_back_to_cart_keeps_user(self):
        page=CheckoutPage.__new__(CheckoutPage);page.frame=Mock();page.root=Mock();page.user_id=1;page.username='customer';page.back_callback=Mock()
        with patch('ui.checkout.CartPage') as cart:page.back();cart.assert_called_once_with(page.root,1,'customer',page.back_callback)

if __name__=='__main__':unittest.main()
