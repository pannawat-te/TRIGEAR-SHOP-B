"""ทดสอบอีเมลแบบจำลอง ไม่เชื่อมต่อ Gmail และไม่ส่งถึงลูกค้า"""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from email.parser import BytesParser
from email import policy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.email_sender import build_otp_message,send_otp

class EmailTests(unittest.TestCase):
    def test_both_templates(self):
        for purpose,title in [('register','ยืนยันอีเมลเพื่อสมัครสมาชิก'),('reset','รหัส OTP สำหรับตั้งรหัสผ่านใหม่')]:
            message=build_otp_message('shop@example.com','customer@example.com','012345',purpose)
            # ทดสอบ MIME ที่ผ่านการ serialize เช่นเดียวกับที่ SMTP รับ
            message=BytesParser(policy=policy.default).parsebytes(message.as_bytes())
            self.assertIn(title,str(message['Subject']))
            self.assertEqual(message['To'],'customer@example.com')
            for kind in ('plain','html'):
                part=message.get_body(preferencelist=(kind,));self.assertIsNotNone(part)
                content=part.get_content()
                self.assertIn('012345',content);self.assertIn('10 นาที',content)
                self.assertIn('ผู้ดูแลระบบ',content);self.assertIn('TRIGEAR',content)
            html=message.get_body(preferencelist=('html',)).get_content()
            self.assertNotIn('<script',html);self.assertNotIn('https://',html)
            images=[part for part in message.walk() if part.get_content_maintype()=='image']
            self.assertEqual(len(images),1)
            self.assertIn(images[0]['Content-ID'][1:-1],html)
            self.assertEqual(images[0].get_content_disposition(),'inline')
    def test_missing_logo_falls_back(self):
        with patch('PIL.Image.open',side_effect=FileNotFoundError):
            message=build_otp_message('shop@example.com','c@example.com','000001','register')
        self.assertIn('TRIGEAR',message.get_body(preferencelist=('html',)).get_content())
        self.assertFalse(any(p.get_content_maintype()=='image' for p in message.walk()))
    def test_mock_smtp(self):
        with patch('services.email_sender.load_settings',return_value={'email':'shop@example.com','password':'mock'}),patch('services.email_sender.smtplib.SMTP') as smtp:
            send_otp('c@example.com','123456','reset')
            client=smtp.return_value.__enter__.return_value
            client.starttls.assert_called_once();client.login.assert_called_once_with('shop@example.com','mock')
            client.send_message.assert_called_once()
            self.assertIn('ตั้งรหัสผ่านใหม่',str(client.send_message.call_args.args[0]['Subject']))
    def test_validation(self):
        for code in ('<b>123','12345','๑๒๓๔๕๖'):
            with self.assertRaises(ValueError):build_otp_message('s@example.com','c@example.com',code,'register')
        with self.assertRaises(ValueError):build_otp_message('s@example.com','c@example.com','123456','unknown')

if __name__=='__main__':unittest.main()
