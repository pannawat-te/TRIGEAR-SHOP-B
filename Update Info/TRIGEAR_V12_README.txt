TRI GEAR V12
Cart and product details follow the supplied PDF.
Cart: clickable product names, inline size selector, unit price, quantity and subtotal.
Details: gallery and thumbnails on the left; description with its own scrollbar on the right.
Size controls only appear on sized products. Quantity additions check stock atomically.
Order history: product image, current product name, recorded size, quantity, recorded unit price and subtotal.
Older product names were not stored in order_items: the current product name is displayed.

Back up database/shop.db and uploads before upgrading.
Copy your current database and uploads into the new TRIGear folder.
Run: py -m pip install -r requirements.txt
Then: py main.py

Checks passed: compilation, imports, quantity/variant stock limits, category migration tests, ZIP integrity.
Windows GUI has not been tested in this environment.
