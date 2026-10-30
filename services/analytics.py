"""สถิติแบบ read-only: ยอดรับชำระตามวันสร้างออเดอร์ และคืนเงินตามวันคืนจริง"""
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from database.database import get_connection
from database.members import require_admin
from services.pricing import amount


def date_range(preset, today=None):
    today=today or date.today()
    if preset=='วันนี้':return today,today
    if preset=='เดือนนี้':return today.replace(day=1),today
    if preset=='ปีนี้':return today.replace(month=1,day=1),today
    raise ValueError('ช่วงเวลาไม่ถูกต้อง')


def local_day(value):
    """CURRENT_TIMESTAMP ของ SQLite เป็น UTC; ISO แบบเดิมในแอปเป็นเวลาท้องถิ่น"""
    from datetime import datetime, timezone
    text=str(value or '')
    if not text:return None
    dt=datetime.fromisoformat(text)
    if dt.tzinfo is not None:dt=dt.astimezone(timezone(timedelta(hours=7)))
    elif 'T' not in text:dt+=timedelta(hours=7)
    return dt.date()


def dashboard_data(admin_id,start,end,category_id=None,ranking='quantity'):
    start=date.fromisoformat(str(start));end=date.fromisoformat(str(end))
    if start>end:raise ValueError('วันที่เริ่มต้นต้องไม่เกินวันที่สิ้นสุด')
    if (end-start).days>3660:raise ValueError('กรุณาเลือกช่วงเวลาไม่เกิน 10 ปี')
    conn=get_connection()
    try:
        require_admin(conn,admin_id)
        conn.execute('BEGIN')
        orders=conn.execute('SELECT id,total_price,subtotal,vat_amount,order_status,payment_status,order_date FROM orders').fetchall()
        chosen=[o for o in orders if (d:=local_day(o[6])) is not None and start<=d<=end]
        paid=[o for o in chosen if o[5]=='ชำระเงินแล้ว']
        gross=sum((amount(o[1]) for o in paid),Decimal(0))
        vat=sum((amount(o[3] or 0) for o in paid),Decimal(0))
        refunded=Decimal(0);refund_by_day=defaultdict(lambda:Decimal(0))
        for value,stamp in conn.execute("SELECT amount,refund_date FROM refunds WHERE refund_status='คืนเงินสำเร็จ'"):
            day=local_day(stamp)
            if day and start<=day<=end:refunded+=amount(value);refund_by_day[day]+=amount(value)
        statuses=defaultdict(int)
        for o in chosen:statuses[o[4]]+=1
        bucket='day' if (end-start).days<=62 else ('month' if (end-start).days<=1096 else 'year')
        def key(d):return d.isoformat() if bucket=='day' else (d.strftime('%Y-%m') if bucket=='month' else str(d.year))
        trend={};d=start
        while d<=end:
            trend.setdefault(key(d),{'sales':Decimal(0),'refunds':Decimal(0),'orders':0});d+=timedelta(days=1)
        for o in chosen:trend[key(local_day(o[6]))]['orders']+=1
        for o in paid:trend[key(local_day(o[6]))]['sales']+=amount(o[1])
        for d,v in refund_by_day.items():trend[key(d)]['refunds']+=v
        valid={o[0] for o in paid if o[4] not in ('ยกเลิกแล้ว','คืนเงินสำเร็จ') and not o[4].startswith('สถานะถูกยกเลิก')}
        products={}
        sql='''SELECT i.order_id,p.id,p.name,i.quantity,i.price FROM order_items i JOIN products p ON p.id=i.product_id'''
        params=()
        if category_id is not None:
            sql+=' WHERE EXISTS (SELECT 1 FROM product_categories pc WHERE pc.product_id=p.id AND pc.category_id=?)';params=(category_id,)
        for oid,pid,name,qty,price in conn.execute(sql,params):
            if oid not in valid:continue
            row=products.setdefault(pid,{'id':pid,'name':name,'quantity':0,'revenue':Decimal(0)})
            row['quantity']+=qty;row['revenue']+=amount(price)*qty
        best=sorted(products.values(),key=lambda x:(-x['quantity'],-x['revenue'],x['id']) if ranking=='quantity' else (-x['revenue'],-x['quantity'],x['id']))[:10]
        categories=conn.execute('SELECT id,name FROM categories ORDER BY name,id').fetchall()
        counts={name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ('products','orders')}
        counts['customers']=conn.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0]
        return dict(gross=gross,vat=vat,subtotal=gross-vat,refunds=refunded,net=gross-refunded,
                    paid_count=len(paid),order_count=len(chosen),statuses=dict(statuses),trend=trend,bucket=bucket,
                    best=best,categories=categories,counts=counts)
    finally:conn.close()
