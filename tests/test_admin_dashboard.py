import sys,tempfile,sqlite3,shutil,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database import database as db
from database.members import set_member_block,block_history,require_active_customer,set_member_role
from services.analytics import dashboard_data,local_day
from datetime import date
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();db.DB_PATH=Path(self.tmp.name)/'shop.db';db.create_tables()
  with db.get_connection() as c:
   c.execute("INSERT INTO users(id,username,email,password,role) VALUES(1,'admin','a@a','hash','admin'),(2,'customer','b@b','hash','customer'),(3,'customer2','c@c','hash','customer')")
   c.execute("INSERT INTO products(id,name,price,stock) VALUES(1,'A',100,10),(2,'B',250,10)")
   c.execute("INSERT INTO categories(id,name) VALUES(1,'shoes')")
   c.execute('INSERT INTO product_categories VALUES(1,1)')
 def tearDown(self):self.tmp.cleanup()
 def test_block(self):
  self.assertTrue(set_member_block(1,2,True,'reason'));self.assertFalse(set_member_block(1,2,True,'reason'))
  with db.get_connection() as c:
   with self.assertRaises(ValueError):require_active_customer(c,2)
  with self.assertRaises(ValueError):set_member_role(1,2,'admin')
  with self.assertRaises(ValueError):set_member_block(1,1,True,'self')
  with self.assertRaises(ValueError):set_member_block(3,2,False,'unauthorized')
  with self.assertRaises(ValueError):set_member_block(1,3,True,' ')
  self.assertTrue(set_member_block(1,2,False,'unblock'))
  self.assertEqual(len(block_history(1,2)),2)
  with db.get_connection() as c:require_active_customer(c,2)
 def test_analytics(self):
  with db.get_connection() as c:
   for oid,total,vat,status,pay,stamp in [(1,214,14,'ยืนยันคำสั่งซื้อ','ชำระเงินแล้ว','2026-10-14 18:00:00'),(2,267.5,17.5,'จัดส่งสำเร็จ','ชำระเงินแล้ว','2026-10-15T12:00:00'),(3,107,7,'กำลังตรวจสอบ','รอตรวจสอบสลิป','2026-10-15T14:00:00'),(4,107,7,'คืนเงินสำเร็จ','ชำระเงินแล้ว','2026-10-15 08:00:00'),(5,50,0,'จัดส่งสำเร็จ','ชำระเงินแล้ว','2026-09-01 08:00:00')]:
    c.execute('INSERT INTO orders(id,user_id,total_price,vat_amount,order_status,payment_status,order_date) VALUES(?,2,?,?,?,?,?)',(oid,total,vat,status,pay,stamp))
   c.executemany('INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)',[(1,1,2,100),(2,2,1,250),(3,1,1,100),(4,1,1,100)])
   c.execute("INSERT INTO refunds(order_id,amount,refund_status,refund_date) VALUES(4,107,'คืนเงินสำเร็จ','2026-10-15 08:00:00')")
  d=dashboard_data(1,'2026-10-15','2026-10-15')
  self.assertEqual(float(d['gross']),588.5);self.assertEqual(float(d['subtotal']),550);self.assertEqual(float(d['refunds']),107);self.assertEqual(d['order_count'],4)
  self.assertEqual([x['id'] for x in d['best']],[1,2]);self.assertEqual(d['best'][0]['quantity'],2)
  self.assertEqual(d['trend']['2026-10-15']['orders'],4)
  self.assertEqual(dashboard_data(1,'2026-10-15','2026-10-15',ranking='revenue')['best'][0]['id'],2)
  self.assertEqual(len(dashboard_data(1,'2026-10-15','2026-10-15',category_id=1)['best']),1)
  with self.assertRaises(ValueError):dashboard_data(2,'2026-10-15','2026-10-15')
  with self.assertRaises(ValueError):dashboard_data(1,'2026-10-16','2026-10-15')
  self.assertEqual(dashboard_data(1,'2026-11-01','2026-11-30')['best'],[])
 def test_blocked_login(self):
  from unittest.mock import patch,Mock
  from ui.login import LoginPage
  with db.get_connection() as c:c.execute('UPDATE users SET password=? WHERE id=2',(db.hash_password('Test1234'),))
  set_member_block(1,2,True,'blocked')
  page=LoginPage.__new__(LoginPage);page.username=Mock();page.username.get.return_value='customer';page.password=Mock();page.password.get.return_value='Test1234';page.root=Mock();page.frame=Mock()
  with patch('ui.login.messagebox.showerror') as warning:
   page.login();warning.assert_called_once();page.frame.destroy.assert_not_called()
 def test_active_session(self):
  from unittest.mock import Mock,patch
  from main import App
  app=App.__new__(App);app.root=Mock();app.root._session_user_id=2;app.show_login=Mock()
  set_member_block(1,2,True,'blocked')
  with patch('tkinter.messagebox.showwarning') as warning:
   app.check_session();app.show_login.assert_called_once();warning.assert_called_once()
  app.root.after.assert_called_once()
 def test_migration(self):
  with db.get_connection() as c:c.execute('INSERT INTO orders(user_id,total_price) VALUES(2,50)')
  db.create_tables();db.create_tables()
  with db.get_connection() as c:
   self.assertEqual(c.execute('SELECT COUNT(*) FROM users').fetchone()[0],3)
   self.assertEqual(c.execute('SELECT total_price FROM orders').fetchone()[0],50)
   self.assertEqual(c.execute('SELECT is_blocked FROM users WHERE id=2').fetchone()[0],0)
if __name__=='__main__':unittest.main()
