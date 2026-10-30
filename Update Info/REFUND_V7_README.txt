TRI GEAR V7 - Refund workflow

1. Checkout: buyer supplies refund bank, account holder and account number.
2. Cancellation before shipment: if paid, creates one pending refund and restores stock only if previously deducted. If not paid, cancels without a refund record.
3. Admin Orders: select order, click "ดู / แนบสลิปคืนเงิน"; bank details and amount appear. After transferring money externally, attach an image and confirm.
4. Customer Order History: completed refund shows "ดูสลิปคืนเงิน" in the same order.

Important: This application does NOT send bank transfers or verify bank transactions. Admin must transfer manually and check the transaction. Account numbers are stored locally in SQLite; protect backups and limit access. Old orders without bank information need manual coordination.

Back up database/shop.db and uploads/ before upgrading. Do not overwrite your real database with the demo database included in this ZIP.
