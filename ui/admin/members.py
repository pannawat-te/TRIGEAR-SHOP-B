from ui.modern_widgets import ActionButton,RoundedCard
# ไฟล์นี้: ค้นหาสมาชิกและเปิดข้อมูลติดต่อ ที่อยู่ ออเดอร์ และคำขอรีเซ็ต
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from database.members import list_members,member_detail,set_member_role,set_member_block,block_history
from ui.customer_style import header,scroll_body

# คลาส AdminMembersPage: เก็บข้อมูลและพฤติกรรมของ ค้นหาสมาชิกและเปิดข้อมูลติดต่อ ที่อยู่ ออเดอร์ และคำขอรีเซ็ต
class AdminMembersPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,admin_id,back):
        self.root=root;self.admin_id=admin_id;self.back=back
        self.frame=tk.Frame(root);self.frame.pack(fill='both',expand=True)
        header(self.frame,'จัดการสมาชิก',self.go_back)
        search=tk.Frame(self.frame);search.pack(fill='x',padx=20,pady=12)
        tk.Label(search,text='ค้นหา Username / อีเมล / เบอร์โทร').pack(side='left')
        self.query=tk.StringVar();field=ttk.Entry(search,textvariable=self.query,width=35);field.pack(side='left',padx=10)
        field.bind('<Return>',lambda e:self.load())
        ActionButton(search,text='ค้นหา',command=self.load).pack(side='left')
        ActionButton(search,text='แสดงทั้งหมด',command=self.clear_search).pack(side='left',padx=8)
        self.count=tk.Label(self.frame);self.count.pack(anchor='w',padx=20)
        box=tk.Frame(self.frame);box.pack(fill='both',expand=True,padx=20,pady=10)
        cols=('username','email','phone','date','orders','requests','role','status')
        self.tree=ttk.Treeview(box,columns=cols,show='headings',selectmode='browse')
        for col,title in zip(cols,('Username','อีเมล','เบอร์โทรติดต่อ','วันที่สมัคร','คำสั่งซื้อ','คำขอรอดำเนินการ','Role','สถานะบัญชี')):
            self.tree.heading(col,text=title);self.tree.column(col,width=160 if col in ('username','email','date') else 110)
        sy=ttk.Scrollbar(box,command=self.tree.yview);sy.pack(side='right',fill='y')
        sx=ttk.Scrollbar(box,orient='horizontal',command=self.tree.xview);sx.pack(side='bottom',fill='x')
        self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set);self.tree.pack(fill='both',expand=True)
        self.tree.bind('<Double-1>',lambda e:self.detail())
        actions=tk.Frame(self.frame);actions.pack(pady=12)
        ActionButton(actions,text='ดูรายละเอียดสมาชิก',command=self.detail).pack(side='left',padx=6)
        ActionButton(actions,text='ตั้งเป็น Admin',command=lambda:self.change_role('admin')).pack(side='left',padx=6)
        ActionButton(actions,text='ตั้งเป็น Customer',command=lambda:self.change_role('customer')).pack(side='left',padx=6)
        ActionButton(actions,text='บล็อกลูกค้า',fg='#B91C1C',command=lambda:self.change_block(True)).pack(side='left',padx=6)
        ActionButton(actions,text='ปลดบล็อก',command=lambda:self.change_block(False)).pack(side='left',padx=6)
        self.load()
    # def clear_search: ล้างคำค้น แล้วโหลดสมาชิกทั้งหมดอีกครั้ง
    def clear_search(self):self.query.set('');self.load()
    # def load: อ่านข้อมูลล่าสุดจากฐานข้อมูล แล้วเติมรายการในหน้าจอ
    def load(self):
        try:rows=list_members(self.admin_id,self.query.get())
        except ValueError as exc:messagebox.showwarning('สมาชิก',str(exc));return
        self.tree.delete(*self.tree.get_children())
        for row in rows:self.tree.insert('','end',iid=str(row[0]),values=(*row[1:-1], 'ถูกบล็อก' if row[-1] else 'ใช้งาน'))
        self.count.config(text=f'พบสมาชิก {len(rows)} คน')
    # def detail: อ่านสมาชิกที่เลือกในตาราง แล้วเปิดรายละเอียดของบัญชีนั้น
    def detail(self):
        selection=self.tree.selection()
        if not selection:messagebox.showwarning('สมาชิก','กรุณาเลือกสมาชิก');return
        show_member_detail(self.root,self.admin_id,int(selection[0]))
    # def change_role: ยืนยันบัญชีที่เลือกก่อนเปลี่ยน Role แล้วโหลดรายชื่อใหม่
    def change_role(self,role):
        selection=self.tree.selection()
        if not selection:messagebox.showwarning('Role','กรุณาเลือกสมาชิก');return
        uid=int(selection[0]);username=self.tree.item(selection[0])['values'][0]
        if not messagebox.askyesno('ยืนยันเปลี่ยน Role',f'เปลี่ยนบทบาทของ {username} (#{uid}) เป็น {role} ใช่หรือไม่?'):return
        try:changed=set_member_role(self.admin_id,uid,role)
        except ValueError as exc:messagebox.showwarning('Role',str(exc));return
        messagebox.showinfo('Role','เปลี่ยนบทบาทแล้ว มีผลกับเมนูเมื่อเข้าสู่ระบบครั้งถัดไป' if changed else 'บัญชีนี้มีบทบาทที่เลือกอยู่แล้ว')
        self.load()
        if self.tree.exists(str(uid)):self.tree.selection_set(str(uid));self.tree.see(str(uid))

    def change_block(self,blocked):
        selected=self.tree.selection()
        if not selected:messagebox.showwarning('สมาชิก','กรุณาเลือกสมาชิก');return
        uid=int(selected[0]);name=self.tree.item(selected[0])['values'][0]
        action='บล็อก' if blocked else 'ปลดบล็อก'
        reason=simpledialog.askstring(action,f'ระบุเหตุผลที่{action} {name} (เก็บในประวัติ Admin):',parent=self.root)
        if reason is None:return
        try:
            changed=set_member_block(self.admin_id,uid,blocked,reason)
            messagebox.showinfo('สมาชิก','บันทึกแล้ว' if changed else 'บัญชีอยู่ในสถานะนี้แล้ว')
            self.load()
        except ValueError as exc:messagebox.showwarning('สมาชิก',str(exc))

    # def go_back: ปิดหน้าปัจจุบัน แล้วเรียกหน้าที่ส่ง callback เข้ามา
    def go_back(self):self.frame.destroy();self.back()

# def show_member_detail: เปิดหน้าต่างรายละเอียดสมาชิกและประวัติ โดยอ่านข้อมูลผ่านการตรวจสิทธิ์ Admin
def show_member_detail(root,admin_id,user_id):
    try:user,address,orders,requests,items=member_detail(admin_id,user_id)
    except ValueError as exc:messagebox.showwarning('สมาชิก',str(exc));return
    dialog=tk.Toplevel(root);dialog.title('รายละเอียดสมาชิก');dialog.geometry('850x620');dialog.transient(root)
    ActionButton(dialog,text='ปิด',command=dialog.destroy).pack(side='bottom',pady=10)
    body=scroll_body(dialog)
    # def label: สร้างข้อความหนึ่งส่วนในหน้ารายละเอียด; bold ใช้กำหนดหัวข้อเป็นตัวหนา
    def label(text,bold=False):
        tk.Label(body,text=text,justify='left',anchor='w',wraplength=760,bg='#F3F5F9',font=('Segoe UI',12,'bold' if bold else 'normal')).pack(fill='x',padx=25,pady=7)
    label(f'สมาชิก #{user[0]} · {user[1]}',True)
    label(f'อีเมล: {user[2]}\nเบอร์โทรติดต่อ: {user[3] or "ยังไม่ระบุ"}\nบทบาท: {user[4]}\nวันที่สมัคร: {user[5]}')
    label('ใช้เบอร์หรืออีเมลในบัญชีเพื่อติดต่อกลับและยืนยันเจ้าของบัญชี ก่อนรีเซ็ตรหัสผ่าน')
    history=block_history(admin_id,user_id)
    label('สถานะบัญชีและประวัติบล็อก',True)
    if not history:label('ใช้งาน · ไม่มีประวัติการบล็อก')
    else:
        label('สถานะ: '+('ถูกบล็อก' if history[0][2]=='block' else 'ใช้งาน'))
        ActionButton(body,text=f'ดูประวัติบล็อก / ปลดบล็อก ({len(history)} รายการ)',
                  command=lambda:show_block_history(dialog,admin_id,user_id)).pack(pady=6)
    label('ที่อยู่จัดส่งที่บันทึกไว้',True)
    label(('ผู้รับ: '+address[0]+' · โทร '+address[1]+'\n'+' '.join(address[2:])) if address else 'ยังไม่บันทึกที่อยู่')
    buttons=tk.Frame(body,bg='#F3F5F9');buttons.pack(fill='x',padx=25,pady=16)
    ActionButton(buttons,text=f'ประวัติคำสั่งซื้อ ({len(orders)} รายการ)',
              command=lambda:show_member_history(dialog,admin_id,user_id,'orders')).pack(fill='x',pady=6,ipady=8)
    ActionButton(buttons,text=f'ประวัติคำขอรีเซ็ตรหัสผ่าน ({len(requests)} รายการ)',
              command=lambda:show_member_history(dialog,admin_id,user_id,'requests')).pack(fill='x',pady=6,ipady=8)

# def show_member_history: อ่านข้อมูลล่าสุดพร้อมตรวจสิทธิ์ Admin แล้วแสดงเฉพาะประวัติที่เลือก
# แยกหน้าต่างเพื่อไม่ให้รายการ Order ยาวผลักประวัติรีเซ็ตลงไปด้านล่าง
def show_member_history(parent,admin_id,user_id,kind):
    try:user,address,orders,requests,items=member_detail(admin_id,user_id)
    except ValueError as exc:messagebox.showwarning('สมาชิก',str(exc));return
    title='ประวัติคำสั่งซื้อ' if kind=='orders' else 'ประวัติคำขอรีเซ็ตรหัสผ่าน'
    win=tk.Toplevel(parent);win.title(f'{title} · {user[1]}');win.geometry('850x620');win.transient(parent)
    tk.Label(win,text=f'{title} · {user[1]}',font=('Segoe UI',16,'bold')).pack(pady=12)
    ActionButton(win,text='ปิด',command=win.destroy).pack(side='bottom',pady=10)
    body=scroll_body(win)
    # def history_label: แสดงข้อความเต็มโดยตัดบรรทัดตามขนาดหน้าต่าง
    def history_label(text,bold=False):
        widget=tk.Label(body,text=text,justify='left',anchor='w',wraplength=760,bg='#F3F5F9',font=('Segoe UI',12,'bold' if bold else 'normal'))
        widget.pack(fill='x',padx=25,pady=7)
        widget.bind('<Configure>',lambda e,w=widget:w.configure(wraplength=max(150,e.width-12)))
    if kind=='orders':
        history_label(f'ทั้งหมด {len(orders)} คำสั่งซื้อ',True)
        if not orders:history_label('ยังไม่มีคำสั่งซื้อ')
        for order in orders:
            history_label(f'#{order[0]} · {order[1]} · ฿{order[2]:,.2f}\nสถานะ: {order[3]} · ชำระเงิน: {order[4]}',True)
            for name,size,quantity,price in items.get(order[0],[]):
                history_label(f'{name}'+(f' · ไซซ์ {size}' if size else '')+f' · {quantity} ชิ้น × ฿{price:,.2f}')
    else:
        history_label(f'ทั้งหมด {len(requests)} คำขอ',True)
        statuses={'pending':'รอดำเนินการ','completed':'ดำเนินการแล้ว','rejected':'ปฏิเสธแล้ว','otp_sent':'ส่ง OTP แล้ว','expired':'OTP หมดอายุ'}
        if not requests:history_label('ไม่มีคำขอรีเซ็ตรหัสผ่าน')
        for rid,created,status,processed in requests:
            history_label(f'#{rid} · {created} · {statuses.get(status,status)}'+(f'\nดำเนินการเมื่อ: {processed}' if processed else ''))


def show_block_history(parent,admin_id,user_id):
    rows=block_history(admin_id,user_id)
    win=tk.Toplevel(parent);win.title('ประวัติบล็อกสมาชิก');win.geometry('780x500')
    body=scroll_body(win)
    for created,admin,action,reason in rows:
        text=f"{created} · {admin} · {'บล็อก' if action=='block' else 'ปลดบล็อก'}\nเหตุผล: {reason}"
        label=tk.Label(body,text=text,anchor='w',justify='left',wraplength=700,padx=20,pady=15)
        label.pack(fill='x',pady=4)
        label.bind('<Configure>',lambda e,w=label:w.configure(wraplength=max(150,e.width-50)))
