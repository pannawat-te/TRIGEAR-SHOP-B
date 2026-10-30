TRI GEAR V11
Run: py -m pip install -r requirements.txt
Then: py main.py

Customer forms: underline inputs with blue focus line.
Updated Account, Register, Checkout, Cart and Order History.
Cart and order lists support vertical scrolling.
Checkout QR is now inside the scrolling page.

Category fix: startup no longer inserts duplicate parent categories.
Existing duplicate siblings merge on startup, preserving product links and children.
A same-name child is displayed as All in this category.

BACK UP database/shop.db and uploads before updating.
To keep your current data, copy your existing database/shop.db and uploads into TRIGear.

Validation: compilation, imports, repeated startup, duplicate merge,
product links, child links and SQLite foreign keys passed on a temporary database.
Windows GUI has not been tested here.
