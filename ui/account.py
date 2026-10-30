from ui.modern_widgets import ActionButton,CheckBox,RadioButton,RoundedCard,option_menu
# ไฟล์นี้: หน้าบัญชีลูกค้า: แก้ Username รหัส เบอร์ติดต่อ และที่อยู่จัดส่ง
from ui.customer_style import entry as customer_entry, header, scroll_body, polish
import tkinter as tk
from tkinter import messagebox
from database.database import get_connection, hash_password
from database.password_policy import valid_password,PASSWORD_HINT
import re
from database.address import ADDRESS_FIELDS, get_address, save_address
from database.customer_defaults import REFUND_FIELDS,get_refund,save_refund


# คลาส AccountPage: เก็บข้อมูลและพฤติกรรมของ หน้าบัญชีลูกค้า
class AccountPage:
    # def __init__: รับข้อมูลที่จำเป็น เก็บไว้ใน self และสร้างองค์ประกอบเริ่มต้นของหน้านี้
    def __init__(self,root,user_id,username,back_callback):
        self.root=root; self.user_id=user_id; self.username=username; self.back_callback=back_callback
        self.frame=tk.Frame(root); self.frame.pack(fill="both",expand=True); self.build()

    # def build: จัดรูปโปรไฟล์ทางซ้ายและฟอร์มข้อมูลเลื่อนแยกทางขวาตามแบบผู้ใช้
    def build(self):
        from ui.shop_style import customer_header,heading,body,card,text,button,form_field,two_columns,BG,WHITE,MUTED
        customer_header(self.frame,self.user_id,self,active='account')
        heading(self.frame,'บัญชีของฉัน','จัดการข้อมูลส่วนตัว รูปโปรไฟล์ ที่อยู่จัดส่ง และบัญชีรับเงินคืน')
        content=body(self.frame);top=tk.Frame(content,bg=BG);top.pack(fill='x')
        left=card(top);right=card(top,'ข้อมูลบัญชี');two_columns(top,left,right,ratio=(1,2),threshold=1050)
        from ui.profile import ProfilePicker
        conn=get_connection()
        try:row=conn.execute('SELECT contact_phone,profile_image,email FROM users WHERE id=?',(self.user_id,)).fetchone()
        finally:conn.close()
        self.profile=ProfilePicker(left,row[1] if row else None,preview_size=220,vertical=True);self.profile.pack(pady=12)
        text(left,self.username,15,True).pack(anchor='center',pady=8)
        text(left,'ครอปรูปก่อนบันทึก · รูปใหม่มีผลเมื่อบันทึกบัญชี',10,color=MUTED).pack(fill='x',pady=6)
        self.user=form_field(right,'ชื่อผู้ใช้ (Username)');self.user.insert(0,self.username)
        email=form_field(right,'อีเมล');email.insert(0,row[2] if row else '');email.configure(state='readonly')
        self.contact_phone=form_field(right,'เบอร์โทรติดต่อ');self.contact_phone.insert(0,row[0] or '' if row else '')
        self.pw=form_field(right,'รหัสผ่านใหม่',show='*',password_chars_only=True)
        self.pw_confirm=form_field(right,'ยืนยันรหัสผ่านใหม่',show='*',password_chars_only=True)
        text(right,'เว้นว่างหากไม่เปลี่ยนรหัสผ่าน · '+PASSWORD_HINT,10,color=MUTED).pack(fill='x',pady=8)
        button(right,'บันทึกบัญชี',self.save).pack(fill='x',pady=10)
        lower=tk.Frame(content,bg=BG);lower.pack(fill='x')
        shipping=card(lower,'ที่อยู่จัดส่งเริ่มต้น');refund_box=card(lower,'บัญชีรับเงินคืนเริ่มต้น')
        two_columns(lower,shipping,refund_box,ratio=(1,1),threshold=1050)
        text(shipping,'ใช้เติมข้อมูลเมื่อชำระเงินครั้งถัดไป',10,color=MUTED).pack(anchor='w',pady=(0,8))
        saved=get_address(self.user_id);self.address_fields={}
        for key,label in ADDRESS_FIELDS:
            var=tk.StringVar(value=saved.get(key,''));self.address_fields[key]=var;form_field(shipping,label,var)
        button(shipping,'บันทึกที่อยู่จัดส่ง',self.save_shipping).pack(fill='x',pady=12)
        saved=get_refund(self.user_id);self.refund_fields={}
        for key,label in REFUND_FIELDS:
            var=tk.StringVar(value=saved.get(key,''));self.refund_fields[key]=var;form_field(refund_box,label,var)
        text(refund_box,'ใช้กับคำสั่งซื้อใหม่ ข้อมูลในคำสั่งซื้อเดิมคงเดิม',10,color=MUTED).pack(fill='x',pady=10)
        button(refund_box,'บันทึกบัญชีรับเงินคืน',self.save_refund_account).pack(fill='x',pady=12)
        button(content,'กลับหน้าร้าน',self.back,'secondary').pack(anchor='w',pady=12)

    # def save: ตรวจข้อมูลที่กรอกและบันทึกการเปลี่ยนแปลงของหน้านี้
    def save(self):
        username=self.user.get().strip(); pw=self.pw.get()
        if pw!=self.pw_confirm.get():messagebox.showwarning('รหัสผ่าน','รหัสผ่านใหม่และการยืนยันไม่ตรงกัน');return
        if len(username)<6: messagebox.showwarning("แจ้งเตือน","Username ต้องมีอย่างน้อย 6 ตัว"); return
        phone=re.sub(r"[\s-]","",self.contact_phone.get().strip())
        if phone and not re.fullmatch(r"0[0-9]{8,9}",phone):
            messagebox.showwarning("เบอร์โทรติดต่อ","กรุณากรอกเบอร์โทรศัพท์ไทย 9–10 หลัก เริ่มด้วย 0");return
        conn=get_connection(); cur=conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=? AND id<>?",(username,self.user_id))
        if cur.fetchone(): conn.close(); messagebox.showerror("ผิดพลาด","Username นี้ถูกใช้งานแล้ว"); return
        if pw:
            if not valid_password(pw):
                conn.close(); messagebox.showwarning("Password",PASSWORD_HINT); return
            cur.execute("UPDATE users SET username=?,password=? WHERE id=?",(username,hash_password(pw),self.user_id))
        else:
            cur.execute("UPDATE users SET username=? WHERE id=?",(username,self.user_id))
        cur.execute("UPDATE users SET contact_phone=? WHERE id=?",(phone or None,self.user_id))
        # บันทึกภาพเฉพาะเมื่อผู้ใช้แก้รูป และเก็บเส้นทางไว้กับบัญชี
        new_path=None
        try:
            if self.profile.changed:
                from ui.profile import save_profile
                new_path=save_profile(self.profile.image) if self.profile.image else None
                cur.execute("UPDATE users SET profile_image=? WHERE id=?",(new_path,self.user_id))
            conn.commit()
        except Exception:
            conn.rollback()
            if new_path:
                from pathlib import Path
                (Path(__file__).resolve().parent.parent/new_path).unlink(missing_ok=True)
            messagebox.showerror("บันทึกบัญชี","บันทึกไม่สำเร็จ กรุณาลองใหม่");return
        finally:conn.close()
        self.username=username
        owner=getattr(self.back_callback,"__self__",None)
        if owner is not None and hasattr(owner,"username"): owner.username=username
        messagebox.showinfo("สำเร็จ","บันทึกข้อมูลแล้ว"); self.back()

    # def save_shipping: อ่านช่องที่อยู่ ตรวจสอบและบันทึกเป็นที่อยู่เริ่มต้นของลูกค้า
    def save_shipping(self):
        try:
            save_address(self.user_id,{key:var.get() for key,var in self.address_fields.items()})
        except ValueError as exc:
            messagebox.showwarning("ข้อมูลจัดส่ง",str(exc)); return
        except Exception:
            messagebox.showerror("บันทึกที่อยู่","บันทึกไม่สำเร็จ กรุณาลองอีกครั้ง"); return
        messagebox.showinfo("สำเร็จ","บันทึกที่อยู่จัดส่งแล้ว ครั้งถัดไป Checkout จะเติมให้อัตโนมัติ")

    # def save_refund_account: ตรวจและบันทึกข้อมูลบัญชีรับเงินคืนเฉพาะผู้ใช้ปัจจุบัน
    def save_refund_account(self):
        try:save_refund(self.user_id,{key:var.get() for key,var in self.refund_fields.items()})
        except ValueError as exc:messagebox.showwarning("บัญชีรับเงินคืน",str(exc));return
        except Exception:messagebox.showerror("บัญชีรับเงินคืน","บันทึกไม่สำเร็จ กรุณาลองใหม่");return
        messagebox.showinfo("สำเร็จ","บันทึกบัญชีรับเงินคืนแล้ว ใช้กับคำสั่งซื้อครั้งถัดไป")

    # def back: ทำลายหน้าปัจจุบัน แล้วเรียก callback เพื่อย้อนกลับไปหน้าก่อนหน้า
    def back(self):
        self.frame.destroy(); self.back_callback()
