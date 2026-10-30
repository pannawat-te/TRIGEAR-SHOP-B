"""Real Tk/CTk smoke tests. Requires a desktop display; no production DB changes.
Run: py tests/test_ctk_ui.py
"""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tkinter as tk
import customtkinter as ctk
from database import database as db
from ui.theme import apply_theme
from ui.modern_widgets import ActionButton,RoundedCard,SizeChoice
from ui.cart import CartPage

class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:cls.root=tk.Tk()
        except tk.TclError as exc:raise unittest.SkipTest('A desktop display is required: '+str(exc))
        cls.root.geometry('1280x900');apply_theme(cls.root)
        cls.errors=[]
        cls.root.report_callback_exception=lambda *error:cls.errors.append(error)
        cls.root._logout_callback=lambda:None
    @classmethod
    def tearDownClass(cls):cls.root.destroy()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old_db=db.DB_PATH;db.DB_PATH=Path(self.tmp.name)/'shop.db';db.create_tables()
        with db.get_connection() as conn:
            conn.execute("INSERT INTO users(id,username,email,password,role) VALUES(1,'customer','customer@example.com','hash','customer'),(2,'admin','admin@example.com','hash','admin')")
            conn.execute("INSERT INTO products(id,name,price,stock,size_type,image) VALUES(1,'Running shoes long name test',100.1,20,'none','assets/tri_gear_logo.png'),(2,'Shirt',200,10,'clothing','assets/tri_gear_logo.png')")
            conn.execute("INSERT INTO product_variants(id,product_id,size,stock) VALUES(1,2,'M',10)")
        CartPage.carts.clear();CartPage.unchecked.clear();CartPage.loaded_users.clear();self.errors.clear()
    def tearDown(self):
        for w in self.root.winfo_children():w.destroy()
        self.root.update();db.DB_PATH=self.old_db;self.tmp.cleanup()
        CartPage.carts.clear();CartPage.unchecked.clear();CartPage.loaded_users.clear()
    def settle(self):
        self.root.update()
        self.root.after(150,self.root.quit);self.root.mainloop();self.root.update()
        self.assertEqual(self.errors,[])
    def clear(self):
        for w in self.root.winfo_children():w.destroy()
        self.root.update()
    def test_rounded_widgets_and_callbacks(self):
        card=RoundedCard(self.root);card.pack(fill='x')
        state=[];b=ActionButton(card,text='test',command=lambda:state.append(1),bg='white',fg='#4145F1');b.pack()
        self.assertIsInstance(b,ctk.CTkButton);self.assertGreater(b.cget('corner_radius'),0)
        b.invoke();self.assertEqual(state,[1]);b.config(state='disabled');b.invoke();self.assertEqual(state,[1])
        b.configure(bg='#4145F1',fg='white',wraplength=100,height=2)
        self.assertEqual(b.cget('fg_color'),'#4145F1')
        choice=tk.StringVar(value='');size=SizeChoice(card,text='M',variable=choice,value='M');size.pack();size.invoke();self.assertEqual(choice.get(),'M')
        self.settle()
    def test_storefront_details_sizes_and_resize(self):
        from ui.customer_home import CustomerHome
        page=CustomerHome(self.root,1,'customer',lambda:None);self.settle()
        page.details(2);self.settle();page.back_from_details();self.settle()
        self.root.geometry('1000x700');self.settle();self.root.geometry('1280x900');self.settle()
    def test_cart_checkout_review_account_orders_contact(self):
        from ui.checkout import CheckoutPage
        from ui.account import AccountPage
        from ui.orders import OrdersPage
        from ui.contact import ContactPage
        CartPage.add_item(1,1,quantity=2);CartPage.add_item(1,2,1)
        CartPage(self.root,1,'customer',lambda:None);self.settle();self.clear()
        page=CheckoutPage(self.root,1,'customer',lambda:None);self.settle()
        fields=dict(shipping_name='Test',shipping_phone='0812345678',shipping_address='123',shipping_subdistrict='A',shipping_district='B',shipping_province='C',shipping_postcode='40000')
        page.show_review(page.review_items(),fields,'Bank','Test','1234567890');self.settle();page.edit_checkout();self.settle();self.clear()
        for cls in (AccountPage,OrdersPage):cls(self.root,1,'customer',lambda:None);self.settle();self.clear()
        ContactPage(self.root,lambda:None,user_id=1,username='customer');self.settle()
    def test_login_and_register(self):
        from ui.login import LoginPage
        from ui.register import RegisterPage
        LoginPage(self.root,lambda:None);self.settle();self.clear()
        RegisterPage(self.root,lambda:None);self.settle()
    def test_admin_dashboard(self):
        from ui.admin.dashboard import AdminDashboard
        AdminDashboard(self.root,lambda:None,2);self.settle()

if __name__=='__main__':unittest.main()
