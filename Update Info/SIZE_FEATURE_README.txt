TRI GEAR - Size support

Admin > Product Management:
- size_type: none = no size; shoe_cm = shoe size in CM; clothing = clothing size XS-XXL.
- Enter one size and stock per line: 25.0=3 or M=5.
- Total stock for sized products is calculated from the sizes.
- For products already having orders, avoid changing/removing sizes without reconciling outstanding orders.

Customer:
- Select a size on the product details page before adding to cart.
- Different sizes of the same product remain separate cart lines.
- Size is saved on order_items and displayed in admin order details.

Backup database/shop.db and uploads before replacing an existing installation.
The included database is for demonstration; preserve your existing database if you have real data.

Run: py -m pip install -r requirements.txt
     py main.py
