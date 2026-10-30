"""องค์ประกอบหน้าร้านที่ใช้ร่วมกันทุกหน้า โดยไม่ผูกกับข้อมูลสมมติในภาพตัวอย่าง"""
import tkinter as tk
from tkinter import ttk
from ui.modern_widgets import ActionButton,RoundedCard,CheckBox
from ui.customer_style import scroll_body,entry

NAVY='#14253D';BLUE='#4145F1';BG='#F3F5FA';WHITE='#FFFFFF';MUTED='#64748B';BORDER='#E0E6F0'


def text(parent,value='',size=11,bold=False,color=NAVY,**kwargs):
    label=tk.Label(parent,text=value,bg=parent.cget('bg'),fg=color,
        font=('Noto Sans Thai',size,'bold' if bold else 'normal'),anchor='w',justify='left',**kwargs)
    label.bind('<Configure>',lambda e:label.configure(wraplength=max(100,parent.winfo_width()-24)))
    return label


def button(parent,title,command,kind='primary',**kwargs):
    colors={'primary':(BLUE,WHITE,'#3236CD'),'secondary':(WHITE,BLUE,'#EEEDFF'),
        'danger':(WHITE,'#C62836','#FFF0F1'),'muted':('#EEF0F7',NAVY,'#E2E6F0')}
    bg,fg,hover=colors[kind]
    b=ActionButton(parent,text=title,command=command,bg=bg,fg=fg,
        activebackground=hover,highlightthickness=0 if kind in ('primary','muted') else 1,
        highlightbackground=BORDER,**kwargs)
    return b


def card(parent,title=None,**kwargs):
    c=RoundedCard(parent,bg=WHITE,highlightbackground=BORDER,highlightthickness=1,padx=20,pady=18,**kwargs)
    if title:text(c,title,16,True).pack(anchor='w',pady=(0,14))
    return c


def divider(parent):tk.Frame(parent,bg=BORDER,height=1).pack(fill='x',pady=12)


def heading(parent,title,subtitle=None):
    box=tk.Frame(parent,bg=BG);box.pack(fill='x',padx=26,pady=(20,14))
    text(box,title,25,True).pack(anchor='w')
    if subtitle:text(box,subtitle,10,color=MUTED).pack(anchor='w',pady=(5,0))
    return box


def body(parent):
    inner=scroll_body(parent);inner.configure(bg=BG)
    content=tk.Frame(inner,bg=BG,padx=24,pady=6);content.pack(fill='both',expand=True)
    return content


def two_columns(parent,left,right,ratio=(3,2),threshold=1040):
    """ยุบเป็นแนวตั้งเมื่อหน้าต่างแคบ ทั้งสองส่วนอยู่ภายในพื้นที่เลื่อนได้"""
    parent.columnconfigure(0,weight=ratio[0]);parent.columnconfigure(1,weight=ratio[1])
    left.grid(row=0,column=0,sticky='nsew',padx=(0,18),pady=(0,18))
    right.grid(row=0,column=1,sticky='new',pady=(0,18))
    state={'wide':None}
    def adapt(e):
        wide=e.width>=threshold
        if state['wide']==wide:return
        state['wide']=wide
        if wide:
            parent.columnconfigure(0,weight=ratio[0]);parent.columnconfigure(1,weight=ratio[1])
            left.grid_configure(row=0,column=0,columnspan=1,padx=(0,18))
            right.grid_configure(row=0,column=1,columnspan=1)
        else:
            parent.columnconfigure(0,weight=1);parent.columnconfigure(1,weight=0)
            left.grid_configure(row=0,column=0,columnspan=2,padx=0)
            right.grid_configure(row=1,column=0,columnspan=2)
    parent.bind('<Configure>',adapt,add='+')


def form_field(parent,label,variable=None,**kwargs):
    line=tk.Frame(parent,bg=WHITE);line.pack(fill='x',pady=5)
    text(line,label,10,color=MUTED).pack(anchor='w',pady=(0,3))
    control=entry(line,textvariable=variable,**kwargs);control.pack(fill='x',pady=(0,4))
    return control


def money_summary(parent,base,vat,total,quantity=None):
    c=card(parent,'รายการสรุป')
    if quantity is not None:text(c,f'เลือกแล้ว {quantity} ชิ้น',12,True).pack(anchor='w',pady=(0,12))
    labels=[]
    for title,value in [('ราคาสินค้าก่อน VAT',base),('VAT 7%',vat)]:
        row=tk.Frame(c,bg=WHITE);row.pack(fill='x',pady=7)
        text(row,title,11,color=MUTED).pack(side='left')
        val=text(row,f'฿{value:,.2f}',12,True);val.pack(side='right');labels.append(val)
    divider(c)
    text(c,'รวมชำระ',12,True).pack(anchor='w')
    val=text(c,f'฿{total:,.2f}',25,True,BLUE);val.pack(anchor='w',pady=(5,18));labels.append(val)
    return c,labels


def refresh_badges(root,user_id):
    from ui.cart import CartPage
    def walk(w):
        if getattr(w,'_cart_uid',None)==user_id:w.configure(text=f'ตะกร้า ({CartPage.total_quantity(user_id)})')
        for child in w.winfo_children():walk(child)
    walk(root)


def customer_header(parent,user_id,owner,active='',back=None):
    root=owner.root
    parent.configure(bg=BG)
    nav=RoundedCard(parent,bg=WHITE,padx=14,pady=10,corner_radius=14,highlightbackground=BORDER,highlightthickness=1)
    nav.pack(fill='x',padx=16,pady=(12,0))
    from ui.brand import logo
    image=logo((112,50));brand=tk.Label(nav,image=image,bg=WHITE);brand.image=image;brand.pack(side='left')
    def go(name):
        from database.database import get_connection
        conn=get_connection()
        try:r=conn.execute('SELECT username FROM users WHERE id=?',(user_id,)).fetchone()
        finally:conn.close()
        username=r[0] if r else getattr(owner,'username','')
        owner.frame.destroy()
        logout=getattr(root,'_logout_callback',getattr(root,'_customer_logout',None))
        from ui.customer_home import CustomerHome
        def home():CustomerHome(root,user_id,username,logout)
        if name=='home':home()
        elif name=='cart':
            from ui.cart import CartPage
            CartPage(root,user_id,username,home)
        elif name=='orders':
            from ui.orders import OrdersPage
            OrdersPage(root,user_id,username,home)
        elif name=='account':
            from ui.account import AccountPage
            AccountPage(root,user_id,username,home)
        else:
            from ui.contact import ContactPage
            ContactPage(root,home,user_id=user_id,username=username)
    logout=getattr(root,'_logout_callback',None) or getattr(root,'_customer_logout',None)
    button(nav,'ออกจากระบบ',logout or getattr(owner,'logout_callback',lambda:None),'danger').pack(side='right',padx=(12,0))
    from database.database import get_connection
    conn=get_connection()
    try:r=conn.execute('SELECT profile_image FROM users WHERE id=?',(user_id,)).fetchone()
    finally:conn.close()
    from ui.avatar import avatar_image
    from PIL import ImageTk
    avatar=ImageTk.PhotoImage(avatar_image(r[0] if r else None,size=42))
    account=tk.Button(nav,image=avatar,command=lambda:go('account'),bg=WHITE,bd=0,padx=0,pady=0,cursor='hand2');account.image=avatar;account.pack(side='right',padx=8)
    from ui.cart import CartPage
    count=button(nav,f'ตะกร้า ({CartPage.total_quantity(user_id)})',lambda:go('cart'),'secondary');count._cart_uid=user_id;count.pack(side='right',padx=4)
    for title,key in [('Contact','contact'),('คำสั่งซื้อ','orders'),('สินค้าทั้งหมด','home')]:
        b=button(nav,title,lambda k=key:go(k),'muted' if active==key else 'secondary');b.pack(side='right',padx=4)
    if back:
        line=tk.Frame(parent,bg=BG);line.pack(fill='x',padx=26,pady=(12,0))
        button(line,'‹ กลับ',back,'secondary').pack(anchor='w')
    return count
