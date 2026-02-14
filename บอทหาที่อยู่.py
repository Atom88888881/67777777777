import discord
from discord.ext import commands
import requests
import json
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from colorama import init, Fore, Style

init(autoreset=True)

# ค่าคงที่จากโค้ดเดิม
TRUE_USER = "17554398"
TRUE_PASS = "true123456"
COOKIE_FILE = "true_cookies.json"

class TruePortalBot:
    def __init__(self):
        self.config_file = "bot_config.json"
        self.cookies = {}
        self.load_config()
        self.load_cookies()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"{Fore.GREEN}✓ Loaded config from {self.config_file}")
            except Exception as e:
                print(f"{Fore.RED}✗ Config load error: {e}")
                self.config = {}
        else:
            self.config = {}
            self.setup_config()
    
    def load_cookies(self):
        try:
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                    self.cookies = json.load(f)
                print(f"{Fore.GREEN}✓ Loaded cookies from {COOKIE_FILE}")
        except:
            self.cookies = {}
    
    def save_cookies(self):
        try:
            with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f)
            print(f"{Fore.GREEN}✓ Saved cookies to {COOKIE_FILE}")
        except:
            pass
    
    def setup_config(self):
        print(f"\n{Fore.YELLOW}═══════════════════════════════════════")
        print(f"    True Portal Discord Bot Setup")
        print(f"═══════════════════════════════════════{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}Please enter the following information:{Style.RESET_ALL}")
        
        while True:
            token = input(f"{Fore.WHITE}Discord Bot Token: {Fore.YELLOW}").strip()
            if token:
                break
            print(f"{Fore.RED}Token cannot be empty!")
        
        while True:
            channel_id = input(f"{Fore.WHITE}Target Channel ID: {Fore.YELLOW}").strip()
            if channel_id and channel_id.isdigit():
                break
            print(f"{Fore.RED}Please enter a valid numeric Channel ID!")
        
        self.config = {
            "token": token,
            "channel_id": int(channel_id)
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            print(f"{Fore.GREEN}✓ Configuration saved to {self.config_file}")
            print(f"{Fore.GREEN}✓ Bot setup complete!")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to save config: {e}")
            return False
        
        return True
    
    def get_cookies_selenium(self):
        """วิธีที่ 1: ใช้ Selenium สำหรับ login"""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--remote-debugging-port=9222")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = None
        try:
            chrome_driver_path = ChromeDriverManager().install()
            if os.name == 'posix':
                chrome_driver_path = chrome_driver_path.replace('.exe', '')
            
            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get("https://sff-dealer.truecorp.co.th/mnp/")
            time.sleep(5)
            
            user_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username'], input[type='text']"))
            )
            user_field.clear()
            user_field.send_keys(TRUE_USER)
            time.sleep(1)
            
            pass_field = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password']")
            pass_field.clear()
            pass_field.send_keys(TRUE_PASS)
            time.sleep(1)
            
            submit_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .btn-submit"))
            )
            
            try:
                submit_btn.click()
            except:
                driver.execute_script("arguments[0].click();", submit_btn)
            
            time.sleep(10)
            
            if "login" not in driver.current_url.lower():
                cookies = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                if "JSESSIONID" in cookie_dict:
                    self.cookies = cookie_dict
                    self.save_cookies()
                    return True
            return False
            
        except Exception as e:
            print(f"{Fore.RED}✗ Selenium login error: {e}")
            return False
        finally:
            if driver:
                driver.quit()
    
    def get_cookies_direct(self):
        """วิธีที่ 2: ใช้ requests โดยตรง"""
        try:
            session = requests.Session()
            login_page = session.get("https://sff-dealer.truecorp.co.th/mnp/")
            
            csrf_token = None
            if 'csrf' in login_page.text:
                import re
                csrf_match = re.search(r'name="csrf_token".*?value="(.*?)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
            
            form_data = {
                'username': TRUE_USER,
                'password': TRUE_PASS
            }
            
            if csrf_token:
                form_data['csrf_token'] = csrf_token
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = session.post(
                "https://sff-dealer.truecorp.co.th/mnp/login",
                data=form_data,
                headers=headers
            )
            
            if response.status_code == 200:
                cookies = session.cookies.get_dict()
                if cookies:
                    self.cookies = cookies
                    self.save_cookies()
                    return True
                    
        except Exception as e:
            print(f"{Fore.RED}✗ Direct login error: {e}")
        
        return False
    
    def check_login_status(self):
        """ตรวจสอบสถานะการ login"""
        if not self.cookies:
            print(f"{Fore.YELLOW}⏳ No cookies found, logging in...")
            
            if self.get_cookies_selenium():
                print(f"{Fore.GREEN}✓ Login successful (Selenium)")
                return True
            else:
                print(f"{Fore.YELLOW}⏳ Trying alternative method...")
                
                if self.get_cookies_direct():
                    print(f"{Fore.GREEN}✓ Login successful (Direct)")
                    return True
                else:
                    print(f"{Fore.RED}✗ Login failed")
                    return False
        return True
    
    def fetch_data(self, query, retry=True):
        """ดึงข้อมูลจาก API"""
        if not self.cookies:
            if not self.check_login_status():
                return {"error": "Authentication Failed"}
        
        mode = "certificateid" if len(query) == 13 else "product-id-number"
        url = f"https://sff-dealer.truecorp.co.th/profiles/customer/get?{mode}={query}"
        if len(query) == 10:
            url += "&product-id-name=msisdn"
        
        headers = {
            "channel_alias": "WHS",
            "employeeid": TRUE_USER,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            r = requests.get(url, headers=headers, cookies=self.cookies, timeout=15)
            
            if r.status_code == 401 and retry:
                print(f"{Fore.YELLOW}⏳ Session expired, reconnecting...")
                self.cookies = {}
                if self.check_login_status():
                    return self.fetch_data(query, retry=False)
                    
            if r.status_code == 200:
                res = r.json()
                
                # Debug: พิมพ์ข้อมูลที่ได้จาก API
                print(f"{Fore.CYAN}API Response: {json.dumps(res, indent=2, ensure_ascii=False)[:500]}...")
                
                output = {
                    "status": "success",
                    "type": "phone" if len(query) == 10 else "idcard",
                    "value": query,
                    "results": res
                }
                return output
                
            return {"error": f"API Error {r.status_code}"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def extract_address(self, response_data):
        """ดึงข้อมูลที่อยู่จาก response"""
        address_lines = []
        
        # ตรวจสอบหลายรูปแบบของ address
        if "address-list" in response_data:
            addr_list = response_data["address-list"]
            
            # ลองดูหลายๆ ประเภทของ address
            address_types = ["CUSTOMER_ADDRESS", "REGISTRATION_ADDRESS", "CONTACT_ADDRESS", "BILLING_ADDRESS"]
            
            for addr_type in address_types:
                if addr_type in addr_list and addr_list[addr_type]:
                    addr = addr_list[addr_type]
                    if isinstance(addr, dict):
                        parts = []
                        
                        # สร้างที่อยู่แบบเต็ม
                        if addr.get('number') and addr['number'] != '-':
                            parts.append(f"บ้านเลขที่ {addr['number']}")
                        if addr.get('building-name') and addr['building-name'] != '-':
                            parts.append(f"อาคาร {addr['building-name']}")
                        if addr.get('moo') and addr['moo'] != '-':
                            parts.append(f"หมู่ {addr['moo']}")
                        if addr.get('soi') and addr['soi'] != '-':
                            parts.append(f"ซอย {addr['soi']}")
                        if addr.get('street') and addr['street'] != '-':
                            parts.append(f"ถนน {addr['street']}")
                        
                        if parts:
                            address_lines.append("**ที่อยู่:** " + " ".join(parts))
                        
                        # เพิ่มข้อมูลตำบล อำเภอ จังหวัด
                        if addr.get('sub-district') and addr['sub-district'] != '-':
                            address_lines.append(f"**ตำบล/แขวง:** {addr['sub-district']}")
                        if addr.get('district') and addr['district'] != '-':
                            address_lines.append(f"**อำเภอ/เขต:** {addr['district']}")
                        if addr.get('province') and addr['province'] != '-':
                            address_lines.append(f"**จังหวัด:** {addr['province']}")
                        if addr.get('zip') and addr['zip'] != '-':
                            address_lines.append(f"**รหัสไปรษณีย์:** {addr['zip']}")
                        
                        # ถ้าเจอที่อยู่แล้วให้หยุด
                        if address_lines:
                            break
        
        return address_lines
    
    def extract_contact_info(self, response_data):
        """ดึงข้อมูลการติดต่อ"""
        contact_info = []
        
        # เบอร์โทรศัพท์
        phone_fields = ['contact-mobile-number', 'mobile-number', 'phone-number', 'contact-number', 'msisdn']
        for field in phone_fields:
            if field in response_data and response_data[field] and response_data[field] != '-':
                contact_info.append(f"**เบอร์โทร:** {response_data[field]}")
                break
        
        # Customer ID
        if 'customer-id' in response_data and response_data['customer-id']:
            contact_info.append(f"**Customer ID:** {response_data['customer-id']}")
        
        # Customer Level
        if 'customer-level' in response_data and response_data['customer-level']:
            level = response_data['customer-level']
            if level != '-':
                contact_info.append(f"**Customer Level:** {level}")
        
        # อีเมล (ถ้ามี)
        email_fields = ['email', 'contact-email', 'email-address']
        for field in email_fields:
            if field in response_data and response_data[field] and response_data[field] != '-':
                contact_info.append(f"**อีเมล:** {response_data[field]}")
                break
        
        return contact_info
    
    def extract_personal_info(self, response_data):
        """ดึงข้อมูลส่วนตัว"""
        personal_info = []
        
        # ชื่อ-นามสกุล
        firstname = response_data.get('firstname', '')
        lastname = response_data.get('lastname', '')
        if firstname or lastname:
            name = f"{firstname} {lastname}".strip()
            if name:
                personal_info.append(f"**ชื่อ-นามสกุล:** {name}")
        
        # คำนำหน้า
        if 'title' in response_data and response_data['title'] and response_data['title'] != '-':
            personal_info.append(f"**คำนำหน้า:** {response_data['title']}")
        
        # เพศ
        if 'gender' in response_data and response_data['gender']:
            gender_map = {
                'M': 'ชาย',
                'F': 'หญิง',
                'Male': 'ชาย',
                'Female': 'หญิง',
                'ชาย': 'ชาย',
                'หญิง': 'หญิง'
            }
            gender = response_data['gender']
            personal_info.append(f"**เพศ:** {gender_map.get(gender, gender)}")
        
        # วันเกิด
        birth_fields = ['birthdate', 'birth-date', 'date-of-birth', 'dob']
        for field in birth_fields:
            if field in response_data and response_data[field] and response_data[field] != '-':
                personal_info.append(f"**วันเกิด:** {response_data[field]}")
                break
        
        # เลขบัตรประชาชน
        id_fields = ['id-number', 'citizen-id', 'national-id', 'certificate-id']
        for field in id_fields:
            if field in response_data and response_data[field] and response_data[field] != '-':
                personal_info.append(f"**เลขบัตร:** {response_data[field]}")
                break
        
        # สัญชาติ
        if 'nationality' in response_data and response_data['nationality'] and response_data['nationality'] != '-':
            personal_info.append(f"**สัญชาติ:** {response_data['nationality']}")
        
        # อาชีพ
        if 'occupation' in response_data and response_data['occupation'] and response_data['occupation'] != '-':
            personal_info.append(f"**อาชีพ:** {response_data['occupation']}")
        
        return personal_info
    
    def create_embed(self, data, query):
        """สร้าง Discord embed จากข้อมูล"""
        query_type = "📱 เบอร์โทรศัพท์" if len(query) == 10 else "🆔 เลขบัตรประชาชน"
        color = 0xED1C24 if len(query) == 10 else 0x3498db
        
        embed = discord.Embed(
            title=f"{query_type}: {query}",
            color=color,
            timestamp=datetime.now()
        )
        
        if "error" in data:
            embed.add_field(
                name="❌ ข้อผิดพลาด",
                value=f"```{data['error']}```",
                inline=False
            )
            embed.color = 0xe74c3c
            return embed
        
        if "results" in data and data["results"]:
            results = data["results"]
            
            # ถ้าข้อมูลอยู่ใน response-data
            if "response-data" in results:
                response_data = results["response-data"]
                
                # ข้อมูลส่วนตัว
                personal_info = self.extract_personal_info(response_data)
                if personal_info:
                    embed.add_field(
                        name="👤 ข้อมูลส่วนตัว",
                        value="\n".join(personal_info),
                        inline=False
                    )
                
                # ข้อมูลการติดต่อ
                contact_info = self.extract_contact_info(response_data)
                if contact_info:
                    embed.add_field(
                        name="📞 ข้อมูลการติดต่อ",
                        value="\n".join(contact_info),
                        inline=False
                    )
                
                # ที่อยู่
                address_lines = self.extract_address(response_data)
                if address_lines:
                    embed.add_field(
                        name="📍 ที่อยู่",
                        value="\n".join(address_lines),
                        inline=False
                    )
                
                # ข้อมูลเพิ่มเติม (ถ้ามี)
                other_info = []
                
                # วันที่ลงทะเบียน
                reg_fields = ['registration-date', 'register-date', 'created-date']
                for field in reg_fields:
                    if field in response_data and response_data[field] and response_data[field] != '-':
                        other_info.append(f"**วันที่ลงทะเบียน:** {response_data[field]}")
                        break
                
                # ประเภทลูกค้า
                if 'customer-type' in response_data and response_data['customer-type'] and response_data['customer-type'] != '-':
                    other_info.append(f"**ประเภทลูกค้า:** {response_data['customer-type']}")
                
                # สถานะ
                if 'status' in response_data and response_data['status'] and response_data['status'] != '-':
                    other_info.append(f"**สถานะ:** {response_data['status']}")
                
                if other_info:
                    embed.add_field(
                        name="ℹ️ ข้อมูลเพิ่มเติม",
                        value="\n".join(other_info),
                        inline=False
                    )
            
            # ถ้าข้อมูลอยู่ในรูปแบบอื่น
            else:
                # ลองหาข้อมูลจากฟิลด์อื่นๆ
                all_info = []
                for key, value in results.items():
                    if isinstance(value, (str, int, float)) and value and str(value) != '-':
                        all_info.append(f"**{key}:** {value}")
                
                if all_info:
                    embed.add_field(
                        name="📋 ข้อมูลทั้งหมด",
                        value="\n".join(all_info[:10]),  # จำกัดไม่ให้เกิน 10 รายการ
                        inline=False
                    )
        
        embed.set_footer(text=f"True Portal Intelligence • ค้นหาเมื่อ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed
    
    def run_bot(self):
        if not self.config.get("token") or not self.config.get("channel_id"):
            print(f"{Fore.RED}✗ Invalid configuration. Please run setup again.")
            return
        
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"\n{Fore.GREEN}═══════════════════════════════════════")
            print(f"        True Portal Bot is Ready!")
            print(f"═══════════════════════════════════════")
            print(f"Logged in as: {bot.user.name}")
            print(f"Bot ID: {bot.user.id}")
            print(f"Channel ID: {self.config['channel_id']}")
            print(f"Prefix: !")
            print(f"═══════════════════════════════════════{Style.RESET_ALL}\n")
            print(f"{Fore.CYAN}Waiting for commands...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Command: !phone <phone_number>{Style.RESET_ALL}")
            
            # ตรวจสอบ login ตอนเริ่ม bot
            if self.check_login_status():
                print(f"{Fore.GREEN}✓ Connected to True Portal{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Failed to connect to True Portal{Style.RESET_ALL}")
        
        @bot.command(name='atom')
        async def phone_lookup(ctx, phone_number: str = None):
            if str(ctx.channel.id) != str(self.config["channel_id"]):
                return
            
            if not phone_number:
                await ctx.send("**Usage:** `!phone <phone_number>`\nExample: `!phone 0918391017`")
                return
            
            # ตรวจสอบรูปแบบข้อมูล
            if not phone_number.isdigit():
                await ctx.send("❌ **ข้อผิดพลาด:** กรุณากรอกเฉพาะตัวเลขเท่านั้น")
                return
            
            if len(phone_number) != 10:
                await ctx.send("❌ **ข้อผิดพลาด:** เบอร์โทรศัพท์ต้อง 10 หลักเท่านั้น")
                return
            
            # แสดงสถานะกำลังค้นหา
            loading_msg = await ctx.send(f"🔍 **กำลังค้นหาข้อมูลเบอร์** `{phone_number}`...")
            
            try:
                # เรียกดูข้อมูล
                data = self.fetch_data(phone_number)
                
                await loading_msg.delete()
                
                if "error" in data:
                    embed = self.create_embed(data, phone_number)
                    await ctx.send(embed=embed)
                else:
                    embed = self.create_embed(data, phone_number)
                    
                    # สร้างข้อความสรุป
                    summary = f"✅ **พบข้อมูลเบอร์** {phone_number}"
                    
                    await ctx.send(summary, embed=embed)
                    
                    print(f"{Fore.GREEN}✓ Sent phone lookup results for: {phone_number}")
                
            except Exception as e:
                await loading_msg.edit(content=f"❌ **เกิดข้อผิดพลาด:** {str(e)}")
                print(f"{Fore.RED}✗ Error: {e}")
        
        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                return
            
            error_msg = f"**Error:** {str(error)}"
            if len(error_msg) > 2000:
                error_msg = error_msg[:1997] + "..."
            
            await ctx.send(error_msg)
            print(f"{Fore.RED}✗ Command error: {error}")
        
        try:
            print(f"{Fore.CYAN}Starting bot...{Style.RESET_ALL}")
            bot.run(self.config["token"])
        except discord.LoginFailure:
            print(f"{Fore.RED}✗ Invalid bot token. Please check your token in {self.config_file}")
        except Exception as e:
            print(f"{Fore.RED}✗ Bot runtime error: {e}")

def main():
    print(f"{Fore.CYAN}=== True Portal Discord Bot ===")
    
    bot = TruePortalBot()
    
    if not bot.config:
        return
    
    while True:
        print(f"\n{Fore.YELLOW}Options:")
        print(f"1. Start Bot")
        print(f"2. Reconfigure Settings")
        print(f"3. Exit")
        
        choice = input(f"\n{Fore.WHITE}Select option (1-3): {Fore.YELLOW}").strip()
        
        if choice == "1":
            print(f"{Fore.CYAN}Starting bot...{Style.RESET_ALL}")
            bot.run_bot()
            break
        elif choice == "2":
            if bot.setup_config():
                bot.run_bot()
                break
        elif choice == "3":
            print(f"{Fore.CYAN}Exiting...{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()