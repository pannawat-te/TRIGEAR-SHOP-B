# TRI GEAR — Desktop Tkinter

## Windows / VS Code
1. Extract the ZIP, then open the `TRIGear` folder in VS Code.
2. Open Terminal > New Terminal.
3. Run `py -m pip install -r requirements.txt`.
4. Run `py main.py`.
5. On a fresh database only, demo admin login: `admin` / `Admin123` (change password before sharing).

Data is saved to `database/shop.db`. Product images are copied to `uploads/products/` and saved as relative paths. Back up the database and uploads folder together.

**Important:** The payment QR in this student demo is NOT a bank-compatible PromptPay QR and cannot be used for actual payments. Slip verification is manual and does not authenticate bank transactions.

Stock is deducted when admin confirms a paid order, not when it enters the cart. Do not confirm the same order twice.

Requires Python with Tkinter installed and a desktop display. To test syntax: `py -m compileall -q .`.


## Gallery and PromptPay image (2026 update)
- Admin > Products > เพิ่มรูปหลายภาพ: select multiple JPG/PNG/WEBP files, preview using arrows, remove a selected photo, or move it to first position as cover. Save the product to persist files into uploads/products/ and rows in product_images.
- Customer > รายละเอียด: navigate images with left/right buttons; single images disable navigation.
- Existing products.image remains the cover; legacy images are loaded as fallback without erasing old data.
- Checkout shows the provided static Krungthai QR image from assets/krungthai_promptpay.jpg. This image has NOT been bank-verified. Amount is shown separately; the customer must confirm payee and amount in the bank app, and admin must verify the slip. No automated payment confirmation.
- For testing, run: python -m compileall -q . and python main.py on Windows with a desktop environment.
