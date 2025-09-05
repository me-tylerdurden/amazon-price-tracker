from bs4 import BeautifulSoup
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import time
import random
import re
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

class AmazonPriceTracker:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.amazon.in/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Email configuration from environment variables with default values
        self.smtp_address = os.getenv('SMTP_ADDRESS', 'smtp.gmail.com')
        self.email_address = os.getenv('EMAIL_ADDRESS', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # Validate email configuration
        if not all([self.email_address, self.email_password]):
            print("⚠️ Warning: Email configuration missing. Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file")
    
    def get_product_info(self, product_url):
        try:
            time.sleep(random.uniform(1, 3))
            response = requests.get(product_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            title_element = (soup.find('span', {'id': 'productTitle'}) or 
                           soup.find('h1', class_='a-size-large') or
                           soup.find('h1', class_='a-size-medium'))
            
            title = title_element.get_text().strip() if title_element else "Product Title Not Found"
            price = self._extract_price(soup)
            
            return {
                'title': title,
                'price': price,
                'url': product_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Error scraping product: {e}")
            return None
    
    def _extract_price(self, soup):
        # Method 1: Standard price display
        whole = soup.find(class_="a-price-whole")
        fraction = soup.find(class_="a-price-fraction")
        
        if whole and fraction:
            price_text = f"{whole.get_text().strip()}.{fraction.get_text().strip()}"
            price_num = self._clean_price(price_text)
            if price_num:
                return price_num
        
        # Method 2: Single price element
        price_selectors = [
            'a-price-range',
            'a-offscreen',
            'a-price a-text-price a-size-medium a-color-price',
            'a-price-whole'
        ]
        
        for selector in price_selectors:
            element = soup.find(class_=selector)
            if element:
                price_text = element.get_text().strip()
                price_num = self._clean_price(price_text)
                if price_num:
                    return price_num
        
        # Method 3: Search for any price
        price_elements = soup.find_all(string=re.compile(r'₹\s*[\d,]+'))
        for price_text in price_elements:
            price_num = self._clean_price(price_text)
            if price_num:
                return price_num
        
        return None
    
    def _clean_price(self, price_text):
        if not price_text:
            return None
        
        cleaned = re.sub(r'[₹$,\s]', '', price_text)
        numbers = re.findall(r'\d+\.?\d*', cleaned)
        
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                return None
        return None
    
    def send_email_alert(self, product_info, target_price):
        print("\n📧 Attempting to send email alert...")
        
        # Check email configuration
        if not all([self.smtp_address, self.email_address, self.email_password]):
            print("❌ Email configuration missing. Please check your .env file.")
            print(f"SMTP: {'✅' if self.smtp_address else '❌'}")
            print(f"Email: {'✅' if self.email_address else '❌'}")
            print(f"Password: {'✅' if self.email_password else '❌'}")
            return False
            
        if not isinstance(product_info, dict) or not all(k in product_info for k in ['title', 'price', 'url', 'timestamp']):
            print("❌ Invalid product information")
            return False
        
        try:
            print("📧 Setting up email message...")
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.email_address
            msg['Subject'] = f"🎉 Price Alert: {product_info['title'][:50]}..."
            
            html_body = f"""
            <html>
                <body>
                    <h2 style="color: #ff9900;">🎉 Price Drop Alert!</h2>
                    <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; max-width: 600px;">
                        <h3 style="color: #333;">{product_info['title']}</h3>
                        <div style="margin: 20px 0;">
                            <p style="font-size: 24px; color: #B12704; font-weight: bold;">
                                Current Price: ₹{product_info['price']:,.2f}
                            </p>
                            <p style="font-size: 16px; color: #666;">
                                Target Price: ₹{target_price:,.2f}
                            </p>
                            <p style="font-size: 14px; color: {('#B12704' if product_info['price'] > target_price else '#2E8B57')};">
                                Price Difference: ₹{abs(product_info['price'] - target_price):,.2f} 
                                {' above target' if product_info['price'] > target_price else ' below target'}
                            </p>
                        </div>
                        <div style="margin: 20px 0;">
                            <a href="{product_info['url']}" 
                               style="background-color: #ff9900; color: white; padding: 12px 24px; 
                                      text-decoration: none; border-radius: 4px; font-weight: bold;">
                                🛒 Buy Now on Amazon
                            </a>
                        </div>
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="font-size: 12px; color: #999;">
                                Alert triggered on: {product_info['timestamp']}
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            print("📧 Connecting to Gmail SMTP server...")
            with smtplib.SMTP(self.smtp_address, port=587) as server:
                print("📧 Establishing secure connection...")
                server.starttls()
                print("📧 Attempting login...")
                server.login(self.email_address, self.email_password)
                print("📧 Sending email...")
                server.sendmail(self.email_address, self.email_address, msg.as_string())
            
            print(f"✅ Email alert sent successfully!")
            print(f"📧 Sent to: {self.email_address}")
            print(f"💰 Price: ₹{product_info['price']:,.2f}")
            print(f"🎯 Target: ₹{target_price:,.2f}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print("❌ Gmail authentication failed!")
            print("👉 Please check:")
            print("  1. Your Gmail account has 2-Step Verification enabled")
            print("  2. You're using an App Password (not your regular Gmail password)")
            print("  3. The App Password is correctly copied to the .env file")
            print(f"Error details: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print("👉 Additional debugging info:")
            print(f"  SMTP Server: {self.smtp_address}")
            print(f"  Email Address: {self.email_address}")
            print(f"  Password length: {len(self.email_password) if self.email_password else 0} characters")
            return False
    
    def check_price_and_alert(self, product_url, target_price):
        print(f"🔍 Checking price for product...")
        
        product_info = self.get_product_info(product_url)
        
        if not product_info:
            print("❌ Failed to get product information")
            return False
        
        if product_info['price'] is None:
            print("❌ Could not extract price from product page")
            return False
        
        current_price = product_info['price']
        
        print(f"📦 Product: {product_info['title'][:50]}...")
        print(f"💰 Current Price: ₹{current_price:,.2f}")
        print(f"🎯 Target Price: ₹{target_price:,.2f}")
        
        if current_price <= target_price:
            print(f"🎉 Price drop detected! Current: ₹{current_price:,.2f} <= Target: ₹{target_price:,.2f}")
            return self.send_email_alert(product_info, target_price)
        else:
            print(f"💭 Price still above target (₹{current_price:,.2f} > ₹{target_price:,.2f})")
            return False
    
    def monitor_price(self, product_url, target_price, check_interval_minutes=30):
        print(f"🚀 Starting price monitoring...")
        print(f"📍 Product URL: {product_url}")
        print(f"🎯 Target Price: ₹{target_price:,.2f}")
        print(f"⏰ Check Interval: {check_interval_minutes} minutes")
        print("-" * 60)
        
        while True:
            try:
                self.check_price_and_alert(product_url, target_price)
                
                next_check = datetime.fromtimestamp(time.time() + check_interval_minutes * 60)
                print(f"😴 Waiting {check_interval_minutes} minutes until next check...")
                print(f"⏰ Next check at: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 60)
                
                time.sleep(check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Price monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                print("⏰ Retrying in 5 minutes...")
                time.sleep(300)

if __name__ == "__main__":
    tracker = AmazonPriceTracker()
    
    # Test email configuration first
    print("\n=== Testing Email Configuration ===")
    test_info = {
        'title': 'Test Product',
        'price': 132900,
        'url': 'https://www.amazon.in/dp/B0DGHYPFYB',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if tracker.send_email_alert(test_info, 132000):
        print("\n✅ Email test successful! Please check your inbox.")
        print("👉 If you don't see the email:")
        print("  1. Check your Spam folder")
        print("  2. Wait a few minutes as emails can be delayed")
        
        # Start actual price monitoring
        product_url = "https://www.amazon.in/dp/B0DGHYPFYB"
        target_price = 132000  # Alert when price drops below ₹1,32,000
        
        print("\n=== iPhone Price Monitor ===")
        print(f"🎯 Target Price: Below ₹{target_price:,}")
        print(f"⏰ Check Interval: Every 30 minutes")
        print("📧 Email alerts configured")
        print("Press Ctrl+C to stop monitoring")
        print("=" * 50)
        
        tracker.monitor_price(product_url, target_price, check_interval_minutes=30)
    else:
        print("\n❌ Email configuration test failed!")
        print("👉 Please fix the email configuration before starting price monitoring")
