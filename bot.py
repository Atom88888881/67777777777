import discord
from discord.ext import commands
import requests
import json
import os
import time
from datetime import datetime
from colorama import init, Fore, Style
import asyncio

init(autoreset=True)

# ค่าคงที่
TRUE_USER = "17554398"
TRUE_PASS = "true123456"
COOKIE_FILE = "true_cookies.json"
LOGIN_URL = "https://sff-dealer.truecorp.co.th/mnp/j_spring_security_check"
BASE_URL = "https://sff-dealer.truecorp.co.th"

class TruePortalBot:
    def __init__(self):
        self.config_file = "bot_config.json"
        self.session = requests.Session()
        self.cookies = {}
        self.load_config()
        self.load_cookies()
        self.setup_session()
    
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
    
    def setup_session(self):
        """ตั้งค่า session headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': BASE_URL,
            'Referer': f'{BASE_URL}/mnp/'
        })
        
        if self.cookies:
            self.session.cookies.update(self.cookies)
    
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
    
    def login(self):
        """เข้าสู่ระบบ True Portal"""
        try:
            print(f"{Fore.YELLOW}⏳ Logging into True Portal...")
            
            # ไปที่หน้า login ก่อนเพื่อ get cookies
            self.session.get(f"{BASE_URL}/mnp/", timeout=10)
            time.sleep(2)
            
            # ส่งข้อมูล login
            login_data = {
                'username': TRUE_USER,
                'password': TRUE_PASS
            }
            
            response = self.session.post(
                LOGIN_URL,
                data=login_data,
                timeout=15,
                allow_redirects=True
            )
            
            # ตรวจสอบว่า login สำเร็จหรือไม่
            if response.status_code == 200:
                # ตรวจสอบโดยการเรียก API ทดสอบ
                test_response = self.session.get(
                    f"{BASE_URL}/profiles/customer/get?product-id-number=0812345678&product-id-name=msisdn",
                    timeout=10
                )
                
                if test_response.status_code == 200:
                    # บันทึก cookies
                    self.cookies = self.session.cookies.get_dict()
                    self.save_cookies()
                    print(f"{Fore.GREEN}✓ Login successful!")
                    return True
                else:
                    print(f"{Fore.RED}✗ Login failed - Invalid credentials or system error")
                    return False
            else:
                print(f"{Fore.RED}✗ Login failed with status code: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}✗ Login timeout - Server not responding")
            return False
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}✗ Connection error - Cannot reach True Portal")
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Login error: {e}")
            return False
    
    def check_login_status(self):
        """ตรวจสอบสถานะการ login"""
        if not self.cookies:
            return self.login()
        
        # ทดสอบว่า cookies ยังใช้งานได้หรือไม่
        try:
            test_response = self.session.get(
                f"{BASE_URL}/profiles/customer/get?product-id-number=0812345678&product-id-name=msisdn",
                timeout=10
            )
            
            if test_response.status_code == 200:
                return True
            elif test_response.status_code == 401:
                print(f"{Fore.YELLOW}⏳ Session expired, re-logging in...")
                return self.login()
            else:
                print(f"{Fore.YELLOW}⏳ Session invalid, re-logging in...")
                return self.login()
                
        except:
            return self.login()
    
    def fetch_data(self, query):
        """ดึงข้อมูลจาก API"""
        if not self.check_login_status():
            return {"error": "ไม่สามารถเชื่อมต่อกับ True Portal ได้"}
        
        # เลือก mode ตามประเภทข้อมูล
        if len(query) == 13:  # เลขบัตรประชาชน
            url = f"{BASE_URL}/profiles/customer/get?certificateid={query}"
        else:  # เบอร์โทรศัพท์
            url = f"{BASE_URL}/profiles/customer/get?product-id-number={query}&product-id-name=msisdn"
        
        headers = {
            "channel_alias": "WHS",
            "employeeid": TRUE_USER,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        "status": "success",
                        "type": "phone" if len(query) == 10 else "idcard",
                        "value": query,
                        "results": data
                    }
                except:
                    return {"error": "ข้อมูลที่ได้รับไม่ถูกต้อง"}
            elif response.status_code == 401:
                return {"error": "Session หมดอายุ กรุณาลองใหม่อีกครั้ง"}
            elif response.status_code == 404:
                return {"error": "ไม่พบข้อมูลในระบบ"}
            else:
                return {"error": f"API Error {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"error": "การเชื่อมต่อหมดเวลา"}
        except requests.exceptions.ConnectionError:
            return {"error": "ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้"}
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
        
        # สร้าง embed หลัก
        embed = discord.Embed(
            title=f"📡 ข้อมูลลูกค้า True Portal",
            description=f"━━━━━━━━━━━━━━━━━━━━",
            color=0xED1C24,
            timestamp=datetime.now()
        )
        
        if "response-data" in results:
            rd = results["response-data"]
            
            # 【 🙍‍♂️ 】ข้อมูลส่วนบุคคล
            personal_info = []
            
            # ชื่อ-นามสกุล
            firstname = rd.get('firstname', '')
            lastname = rd.get('lastname', '')
            title = rd.get('title', '')
            
            if title and (firstname or lastname):
                name = f"{title} {firstname} {lastname}".strip()
            else:
                name = f"{firstname} {lastname}".strip()
            
            if name and name != ' ':
                personal_info.append(f"👤 **ชื่อ-นามสกุล:** {name}")
            
            # เลขบัตรประชาชน
            id_number = rd.get('id-number', '')
            if id_number and id_number != '-':
                # แสดงเลขบัตรแบบเว้นวรรคทุก 4 หลัก
                formatted_id = ' '.join([id_number[i:i+4] for i in range(0, len(id_number), 4)])
                personal_info.append(f"🪪 **เลขบัตรประชาชน:** {formatted_id}")
            
            # วันเกิด
            birthdate = rd.get('birthdate', '')
            if birthdate and birthdate != '-':
                thai_birth = self.format_thai_date(birthdate)
                personal_info.append(f"📅 **วันเกิด:** {thai_birth}")
            
            # เพศ
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
            
            # เบอร์โทร
            phone = rd.get('contact-mobile-number', '')
            if phone and phone != '-':
                # จัดรูปแบบเบอร์โทร
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
                            
                            # บ้านเลขที่
                            if addr.get('number') and addr['number'] != '-':
                                address_lines.append(f"🏠 **บ้านเลขที่:** {addr['number']}")
                            
                            # หมู่
                            if addr.get('moo') and addr['moo'] != '-':
                                address_lines.append(f"🏘️ **หมู่:** {addr['moo']}")
                            
                            # อาคาร
                            if addr.get('building-name') and addr['building-name'] != '-':
                                address_lines.append(f"🏢 **อาคาร:** {addr['building-name']}")
                            
                            # ซอย
                            if addr.get('soi') and addr['soi'] != '-':
                                address_lines.append(f"🛣️ **ซอย:** {addr['soi']}")
                            
                            # ถนน
                            if addr.get('street') and addr['street'] != '-':
                                address_lines.append(f"🛤️ **ถนน:** {addr['street']}")
                            
                            # ตำบล/แขวง
                            if addr.get('sub-district') and addr['sub-district'] != '-':
                                address_lines.append(f"🗺️ **ตำบล/แขวง:** {addr['sub-district']}")
                            
                            # อำเภอ/เขต
                            if addr.get('district') and addr['district'] != '-':
                                address_lines.append(f"🌆 **อำเภอ/เขต:** {addr['district']}")
                            
                            # จังหวัด
                            if addr.get('province') and addr['province'] != '-':
                                address_lines.append(f"🌇 **จังหวัด:** {addr['province']}")
                            
                            # รหัสไปรษณีย์
                            if addr.get('zip') and addr['zip'] != '-':
                                address_lines.append(f"📮 **รหัสไปรษณีย์:** {addr['zip']}")
                            
                            break  # เจอที่อยู่แล้วหยุด
            
            if address_lines:
                embed.add_field(
                    name="【 📜 】ที่อยู่ตามทะเบียน",
                    value="\n".join(address_lines),
                    inline=False
                )
            
            # 【 💬 】รายละเอียดลูกค้า
            customer_info = []
            
            # รหัสลูกค้า
            customer_id = rd.get('customer-id', '')
            if customer_id and customer_id != '-':
                customer_info.append(f"🆔 **รหัสลูกค้า:** {customer_id}")
            
            # ระดับลูกค้า
            customer_level = rd.get('customer-level', '')
            if customer_level and customer_level != '-':
                customer_info.append(f"⭐ **ระดับลูกค้า:** {customer_level}")
            
            # วันที่บัตรหมดอายุ
            if 'id-card-expire-date' in rd and rd['id-card-expire-date'] and rd['id-card-expire-date'] != '-':
                expire_date = self.format_thai_date(rd['id-card-expire-date'])
                customer_info.append(f"⏳ **บัตรหมดอายุ:** {expire_date}")
            
            if customer_info:
                embed.add_field(
                    name="【 💬 】รายละเอียดลูกค้า",
                    value="\n".join(customer_info),
                    inline=False
                )
        
        # Footer
        current_time = datetime.now()
        thai_time = current_time.strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"Check by: True Portal • {thai_time}")
        
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
        
        @bot.command(name='phone')
        async def phone_lookup(ctx, phone_number: str = None):
            # ตรวจสอบ channel
            if str(ctx.channel.id) != str(self.config["channel_id"]):
                return
            
            # ถ้าไม่มี parameter ส่งข้อความวิธีใช้
            if not phone_number:
                embed = discord.Embed(
                    title="❌ กรุณาใส่เบอร์โทร 10 หลัก",
                    description="**วิธีใช้:** `!phone <เบอร์โทรศัพท์>`\n**ตัวอย่าง:** `!phone 0973105524`",
                    color=0xe74c3c
                )
                await ctx.send(embed=embed)
                return
            
            # ตรวจสอบรูปแบบ
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
            
            # แสดงสถานะกำลังค้นหา
            loading_embed = discord.Embed(
                title=f"🔄 กำลังดึงข้อมูลเบอร์ {phone_number}...",
                description="⏳ กรุณารอสักครู่ ระบบกำลังค้นหาข้อมูล",
                color=0x3498db
            )
            loading_msg = await ctx.send(embed=loading_embed)
            
            try:
                # เรียกดูข้อมูล
                data = self.fetch_data(phone_number)
                
                # ลบข้อความกำลังโหลด
                await loading_msg.delete()
                
                # สร้าง embed สวยงาม
                embed = self.create_beautiful_embed(data, phone_number)
                
                # ส่ง embed
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
