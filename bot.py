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
import asyncio

init(autoreset=True)

# ค่าคงที่
TRUE_USER = "17554398"
TRUE_PASS = "true123456"
COOKIE_FILE = "true_cookies.json"

class TruePortalBot:
    def __init__(self):
        self.token = os.getenv('DISCORD_TOKEN')
        self.channel_id = int(os.getenv('CHANNEL_ID', '0'))
        self.cookies = {}
        self.load_cookies()
        
        if not self.token or not self.channel_id:
            print(f"{Fore.RED}❌ Missing DISCORD_TOKEN or CHANNEL_ID in environment variables")
    
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
                return {
                    "status": "success",
                    "type": "phone" if len(query) == 10 else "idcard",
                    "value": query,
                    "results": res
                }
                
            return {"error": f"API Error {r.status_code}"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def format_thai_date(self, date_str):
        """แปลงวันที่เป็นรูปแบบไทย"""
        if not date_str or date_str == "N/A" or date_str == "-":
            return "-"
        try:
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            thai_months = [
                "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
            ]
            thai_year = date_obj.year + 543
            return f"{date_obj.day} {thai_months[date_obj.month-1]} {thai_year}"
        except:
            return date_str
    
    def create_beautiful_embed(self, data, query):
        """สร้าง Discord embed ที่สวยงาม"""
        
        if "error" in data:
            embed = discord.Embed(
                title=f"❌ ไม่พบข้อมูลเบอร์ {query}",
                description="ระบบไม่พบข้อมูลในฐานข้อมูล",
                color=0xe74c3c,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="📌 สาเหตุ",
                value="• เบอร์โทรศัพท์ไม่อยู่ในระบบ True\n• เบอร์โทรศัพท์ไม่ถูกต้อง\n• ระบบขัดข้องชั่วคราว",
                inline=False
            )
            embed.set_footer(text="Check by: True Portal • กรุณาตรวจสอบเบอร์โทรอีกครั้ง")
            return embed
        
        if "results" not in data or not data["results"]:
            embed = discord.Embed(
                title=f"⚠️ ไม่พบข้อมูลเบอร์ {query}",
                description="กรุณาตรวจสอบเบอร์โทรศัพท์อีกครั้ง",
                color=0xf39c12,
                timestamp=datetime.now()
            )
            embed.set_footer(text="Check by: True Portal")
            return embed
        
        results = data["results"]
        
        embed = discord.Embed(
            title=f"📡 ข้อมูลลูกค้า True Portal",
            description=f"🔄 กำลังดึงข้อมูลเบอร์ **{query}**...\n━━━━━━━━━━━━━━━━━━━━",
            color=0xED1C24,
            timestamp=datetime.now()
        )
        
        if "response-data" in results:
            rd = results["response-data"]
            
            # 【 🙍‍♂️ 】ข้อมูลส่วนบุคคล
            personal_info = []
            
            firstname = rd.get('firstname', '')
            lastname = rd.get('lastname', '')
            title = rd.get('title', '')
            
            if title and (firstname or lastname):
                name = f"{title} {firstname} {lastname}".strip()
            else:
                name = f"{firstname} {lastname}".strip()
            
            if name and name != ' ':
                personal_info.append(f"👤 **ชื่อ-นามสกุล:** {name}")
            
            id_number = rd.get('id-number', '')
            if id_number and id_number != '-':
                formatted_id = ' '.join([id_number[i:i+4] for i in range(0, len(id_number), 4)])
                personal_info.append(f"🪪 **เลขบัตรประชาชน:** {formatted_id}")
            
            birthdate = rd.get('birthdate', '')
            if birthdate and birthdate != '-':
                thai_birth = self.format_thai_date(birthdate)
                personal_info.append(f"📅 **วันเกิด:** {thai_birth}")
            
            gender = rd.get('gender', '')
            if gender:
                gender_map = {
                    'M': 'ชาย', 'F': 'หญิง', 'Male': 'ชาย', 'Female': 'หญิง',
                    'ชาย': 'ชาย', 'หญิง': 'หญิง'
                }
                gender_th = gender_map.get(gender, gender)
                personal_info.append(f"🚻 **เพศ:** {gender_th}")
            
            if personal_info:
                embed.add_field(
                    name="【 🙍‍♂️ 】ข้อมูลส่วนบุคคล",
                    value="\n".join(personal_info),
                    inline=False
                )
            
            # 【 📞 】ข้อมูลการติดต่อ
            contact_info = []
            
            phone = rd.get('contact-mobile-number', '')
            if phone and phone != '-':
                if len(phone) == 10:
                    formatted_phone = f"{phone[0:3]}-{phone[3:6]}-{phone[6:10]}"
                else:
                    formatted_phone = phone
                contact_info.append(f"📱 **เบอร์โทร:** {formatted_phone}")
            
            if contact_info:
                embed.add_field(
                    name="【 📞 】ข้อมูลการติดต่อ",
                    value="\n".join(contact_info),
                    inline=False
                )
            
            # 【 📜 】ที่อยู่ตามทะเบียน
            address_lines = []
            
            if "address-list" in rd:
                addr_list = rd["address-list"]
                address_types = ["CUSTOMER_ADDRESS", "REGISTRATION_ADDRESS", "CONTACT_ADDRESS"]
                
                for addr_type in address_types:
                    if addr_type in addr_list and addr_list[addr_type]:
                        addr = addr_list[addr_type]
                        if isinstance(addr, dict):
                            
                            if addr.get('number') and addr['number'] != '-':
                                address_lines.append(f"🏠 **บ้านเลขที่:** {addr['number']}")
                            
                            if addr.get('moo') and addr['moo'] != '-':
                                address_lines.append(f"🏘️ **หมู่:** {addr['moo']}")
                            
                            if addr.get('building-name') and addr['building-name'] != '-':
                                address_lines.append(f"🏢 **อาคาร:** {addr['building-name']}")
                            
                            if addr.get('soi') and addr['soi'] != '-':
                                address_lines.append(f"🛣️ **ซอย:** {addr['soi']}")
                            
                            if addr.get('street') and addr['street'] != '-':
                                address_lines.append(f"🛤️ **ถนน:** {addr['street']}")
                            
                            if addr.get('sub-district') and addr['sub-district'] != '-':
                                address_lines.append(f"🗺️ **ตำบล/แขวง:** {addr['sub-district']}")
                            
                            if addr.get('district') and addr['district'] != '-':
                                address_lines.append(f"🌆 **อำเภอ/เขต:** {addr['district']}")
                            
                            if addr.get('province') and addr['province'] != '-':
                                address_lines.append(f"🌇 **จังหวัด:** {addr['province']}")
                            
                            if addr.get('zip') and addr['zip'] != '-':
                                address_lines.append(f"📮 **รหัสไปรษณีย์:** {addr['zip']}")
                            
                            break
            
            if address_lines:
                embed.add_field(
                    name="【 📜 】ที่อยู่ตามทะเบียน",
                    value="\n".join(address_lines),
                    inline=False
                )
            
            # 【 💬 】รายละเอียดลูกค้า
            customer_info = []
            
            customer_id = rd.get('customer-id', '')
            if customer_id and customer_id != '-':
                customer_info.append(f"🆔 **รหัสลูกค้า:** {customer_id}")
            
            customer_level = rd.get('customer-level', '')
            if customer_level and customer_level != '-':
                customer_info.append(f"⭐ **ระดับลูกค้า:** {customer_level}")
            
            if 'id-card-expire-date' in rd and rd['id-card-expire-date'] and rd['id-card-expire-date'] != '-':
                expire_date = self.format_thai_date(rd['id-card-expire-date'])
                customer_info.append(f"⏳ **บัตรหมดอายุ:** {expire_date}")
            
            if customer_info:
                embed.add_field(
                    name="【 💬 】รายละเอียดลูกค้า",
                    value="\n".join(customer_info),
                    inline=False
                )
        
        current_time = datetime.now()
        thai_time = current_time.strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"Check by: True Portal • {thai_time}")
        
        return embed
    
    def run_bot(self):
        if not self.token or not self.channel_id:
            print(f"{Fore.RED}✗ Missing Discord Token or Channel ID")
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
            print(f"Channel ID: {self.channel_id}")
            print(f"Prefix: !")
            print(f"═══════════════════════════════════════{Style.RESET_ALL}\n")
            print(f"{Fore.CYAN}Waiting for commands...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Command: !phone <phone_number>{Style.RESET_ALL}")
            
            if self.check_login_status():
                print(f"{Fore.GREEN}✓ Connected to True Portal{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Failed to connect to True Portal{Style.RESET_ALL}")
        
        @bot.command(name='phone')
        async def phone_lookup(ctx, phone_number: str = None):
            if str(ctx.channel.id) != str(self.channel_id):
                return
            
            if not phone_number:
                embed = discord.Embed(
                    title="❌ กรุณาใส่เบอร์โทร 10 หลัก",
                    description="**วิธีใช้:** `!phone <เบอร์โทรศัพท์>`\n**ตัวอย่าง:** `!phone 0973105524`",
                    color=0xe74c3c
                )
                await ctx.send(embed=embed)
                return
            
            if not phone_number.isdigit():
                embed = discord.Embed(
                    title="❌ กรุณาใส่เฉพาะตัวเลข",
                    description="เบอร์โทรศัพท์ต้องเป็นตัวเลขเท่านั้น",
                    color=0xe74c3c
                )
                await ctx.send(embed=embed)
                return
            
            if len(phone_number) != 10:
                embed = discord.Embed(
                    title="❌ กรุณาใส่เบอร์โทร 10 หลัก",
                    description=f"เบอร์ที่ใส่: `{phone_number}` มี {len(phone_number)} หลัก",
                    color=0xe74c3c
                )
                await ctx.send(embed=embed)
                return
            
            loading_embed = discord.Embed(
                title=f"🔄 กำลังดึงข้อมูลเบอร์ {phone_number}...",
                description="⏳ กรุณารอสักครู่ ระบบกำลังค้นหาข้อมูล",
                color=0x3498db
            )
            loading_msg = await ctx.send(embed=loading_embed)
            
            try:
                data = self.fetch_data(phone_number)
                
                await loading_msg.delete()
                
                embed = self.create_beautiful_embed(data, phone_number)
                await ctx.send(embed=embed)
                
                print(f"{Fore.GREEN}✓ Sent phone lookup results for: {phone_number}")
                
            except Exception as e:
                await loading_msg.delete()
                error_embed = discord.Embed(
                    title="❌ เกิดข้อผิดพลาด",
                    description=f"```{str(e)}```",
                    color=0xe74c3c
                )
                await ctx.send(embed=error_embed)
                print(f"{Fore.RED}✗ Error: {e}")
        
        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                return
            
            error_embed = discord.Embed(
                title="❌ ข้อผิดพลาด",
                description=f"```{str(error)}```",
                color=0xe74c3c
            )
            await ctx.send(embed=error_embed)
            print(f"{Fore.RED}✗ Command error: {error}")
        
        try:
            print(f"{Fore.CYAN}Starting bot...{Style.RESET_ALL}")
            bot.run(self.token)
        except discord.LoginFailure:
            print(f"{Fore.RED}✗ Invalid bot token")
        except Exception as e:
            print(f"{Fore.RED}✗ Bot runtime error: {e}")

if __name__ == "__main__":
    bot = TruePortalBot()
    bot.run_bot()
