import json
import asyncio
import re
import random
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Optional, List, Any

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TimedOut, RetryAfter, NetworkError

# config.py dan import
from config import (
    BOT_TOKEN, BOT_NAME, BOT_VERSION, BOT_AUTHOR,
    DEFAULT_INTERVAL, MIN_INTERVAL, MAX_INTERVAL,
    MINUTE, HOUR, DAY,
    QUOTES_FILE, HELP_MESSAGE, START_MESSAGE, ERROR_MESSAGES,
    TIME_MESSAGE, QUOTE_MESSAGE, SUCCESS_MESSAGE,
    READ_TIMEOUT, WRITE_TIMEOUT, CONNECTION_TIMEOUT, POOL_TIMEOUT,
    POLLING_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)

# ============================================
# ADMIN VA REKLAMA KANALLARINI BOSHQARISH
# ============================================

class AdminManager:
    def __init__(self):
        self.super_admin = 5600602320  # O'z ID'ingizni yozing
        self.admins: set = self._load_admins()
        print(f"👑 Superadmin: {self.super_admin}")
        print(f"👥 Adminlar: {len(self.admins)} ta")
    
    def _load_admins(self) -> set:
        try:
            if os.path.exists("admins.json"):
                with open("admins.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('admins', []))
            return set()
        except:
            return set()
    
    def _save_admins(self) -> bool:
        try:
            with open("admins.json", 'w', encoding='utf-8') as f:
                json.dump({'admins': list(self.admins)}, f, ensure_ascii=False, indent=4)
            return True
        except:
            return False
    
    def is_superadmin(self, user_id: int) -> bool:
        return user_id == self.super_admin
    
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins or self.is_superadmin(user_id)
    
    def add_admin(self, user_id: int) -> bool:
        if user_id == self.super_admin:
            return False
        self.admins.add(user_id)
        return self._save_admins()
    
    def remove_admin(self, user_id: int) -> bool:
        if user_id == self.super_admin:
            return False
        if user_id in self.admins:
            self.admins.remove(user_id)
            return self._save_admins()
        return False
    
    def get_admins_list(self) -> list:
        return list(self.admins)

class ChannelManager:
    """REKLAMA KANALLARI - hikmatlar ostida chiqadi"""
    
    def __init__(self):
        self.channels: Dict[str, dict] = self._load_channels()
        print(f"📢 Reklama kanallari: {len(self.channels)} ta")
    
    def _load_channels(self) -> Dict[str, dict]:
        try:
            if os.path.exists("channels.json"):
                with open("channels.json", 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def _save_channels(self) -> bool:
        try:
            with open("channels.json", 'w', encoding='utf-8') as f:
                json.dump(self.channels, f, ensure_ascii=False, indent=4)
            return True
        except:
            return False
    
    def add_channel(self, chat_id: str, title: str, username: str = None):
        self.channels[chat_id] = {
            'id': chat_id,
            'title': title,
            'username': username,
            'added_at': str(datetime.now())
        }
        return self._save_channels()
    
    def remove_channel(self, chat_id: str) -> bool:
        if chat_id in self.channels:
            del self.channels[chat_id]
            return self._save_channels()
        return False
    
    def get_channels(self) -> Dict[str, dict]:
        return self.channels

# ============================================
# ASOSIY KANALLAR - BOT QO'SHILGAN KANALLAR
# ============================================

class BotChannels:
    """Bot to'g'ridan-to'g'ri qo'shilgan kanallar"""
    
    def __init__(self):
        self.channels: Dict[int, dict] = self._load_channels()
        print(f"📢 Bot qo'shilgan kanallar: {len(self.channels)} ta")
    
    def _load_channels(self) -> Dict[int, dict]:
        try:
            if os.path.exists("bot_channels.json"):
                with open("bot_channels.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {int(k): v for k, v in data.items()}
            return {}
        except:
            return {}
    
    def _save_channels(self) -> bool:
        try:
            data = {str(k): v for k, v in self.channels.items()}
            with open("bot_channels.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except:
            return False
    
    def add_channel(self, chat_id: int, title: str, username: str = None, added_by: int = None):
        """Bot qo'shilgan kanalni saqlash"""
        self.channels[chat_id] = {
            'id': chat_id,
            'title': title,
            'username': username,
            'added_at': str(datetime.now()),
            'added_by': added_by,
            'active': True
        }
        return self._save_channels()
    
    def remove_channel(self, chat_id: int) -> bool:
        if chat_id in self.channels:
            del self.channels[chat_id]
            return self._save_channels()
        return False
    
    def get_channels(self) -> Dict[int, dict]:
        return self.channels

# ============================================
# IQTIBOSLAR
# ============================================

class QuoteManager:
    def __init__(self, quotes: List[Dict[str, str]]):
        self.all_quotes = quotes
        self.quotes_by_author = self._group_by_author()
        self.authors = list(self.quotes_by_author.keys())
        self.last_quotes = {}
        self.usage_count = {}
        
        print(f"📊 Mualliflar: {len(self.authors)} ta")
        for author, q_list in self.quotes_by_author.items():
            print(f"   • {author}: {len(q_list)} ta")
    
    def _group_by_author(self) -> Dict[str, List[Dict[str, str]]]:
        groups = defaultdict(list)
        for quote in self.all_quotes:
            groups[quote['author']].append(quote)
        return dict(groups)
    
    def _get_quote_id(self, quote: Dict[str, str]) -> str:
        return f"{quote['text'][:50]}_{quote['author']}"
    
    def _init_chat_stats(self, chat_id: int):
        if chat_id not in self.last_quotes:
            self.last_quotes[chat_id] = deque(maxlen=5)
        if chat_id not in self.usage_count:
            self.usage_count[chat_id] = {
                'total': 0,
                'authors': defaultdict(int),
                'quotes': defaultdict(int)
            }
    
    def get_random_quote(self, chat_id: int) -> Optional[Dict[str, str]]:
        if not self.all_quotes:
            return None
        
        self._init_chat_stats(chat_id)
        
        author_weights = []
        for author in self.authors:
            base_weight = len(self.quotes_by_author[author])
            author_usage = self.usage_count[chat_id]['authors'][author]
            if author_usage > 0:
                weight = base_weight / (author_usage * 2)
            else:
                weight = base_weight * 3
            author_weights.append(max(1, weight))
        
        selected_author = random.choices(self.authors, weights=author_weights)[0]
        author_quotes = self.quotes_by_author[selected_author]
        
        last_ids = [self._get_quote_id(q) for q in self.last_quotes[chat_id]]
        available_quotes = [q for q in author_quotes if self._get_quote_id(q) not in last_ids]
        
        if not available_quotes:
            available_quotes = author_quotes
        
        quote_weights = []
        for quote in available_quotes:
            quote_id = self._get_quote_id(quote)
            quote_usage = self.usage_count[chat_id]['quotes'][quote_id]
            if quote_usage > 0:
                weight = 1 / (quote_usage * 2)
            else:
                weight = 10
            quote_weights.append(max(0.1, weight))
        
        selected_quote = random.choices(available_quotes, weights=quote_weights)[0]
        
        quote_id = self._get_quote_id(selected_quote)
        self.last_quotes[chat_id].append(selected_quote)
        self.usage_count[chat_id]['total'] += 1
        self.usage_count[chat_id]['authors'][selected_author] += 1
        self.usage_count[chat_id]['quotes'][quote_id] += 1
        
        return selected_quote

# ============================================
# JSON FUNKSIYALARI
# ============================================

def load_json_file(file_path: str, default_value: Any = None) -> Any:
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return default_value if default_value is not None else []
    except:
        return default_value if default_value is not None else []

def save_json_file(file_path: str, data: Any) -> bool:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def create_default_quotes() -> List[Dict[str, str]]:
    return [
        {"text": "Ilm olish — har bir muslim va muslimaga farzdir.", "author": "Muhammad (s.a.v.)"}
    ]

# Iqtiboslarni yuklash
QUOTES = load_json_file(QUOTES_FILE, [])
if not QUOTES:
    QUOTES = create_default_quotes()
    save_json_file(QUOTES_FILE, QUOTES)

quote_manager = QuoteManager(QUOTES)
admin_manager = AdminManager()
channel_manager = ChannelManager()  # Reklama kanallari
bot_channels = BotChannels()  # Bot qo'shilgan kanallar

# ============================================
# CHAT SOZLAMALARI
# ============================================

chat_settings: Dict[int, Dict] = {}

def load_chat_settings():
    try:
        if os.path.exists("chat_settings.json"):
            with open("chat_settings.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                result = {}
                for k, v in data.items():
                    chat_id = int(k)
                    if 'next_run' in v and isinstance(v['next_run'], str):
                        v['next_run'] = datetime.fromisoformat(v['next_run'])
                    result[chat_id] = v
                return result
        return {}
    except:
        return {}

def save_chat_settings():
    try:
        data = {}
        for k, v in chat_settings.items():
            chat_data = v.copy()
            if 'task' in chat_data:
                del chat_data['task']
            if 'next_run' in chat_data and isinstance(chat_data['next_run'], datetime):
                chat_data['next_run'] = chat_data['next_run'].isoformat()
            data[str(k)] = chat_data
        
        with open("chat_settings.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

chat_settings = load_chat_settings()

def format_time(seconds: int) -> str:
    hours = seconds // HOUR
    minutes = (seconds % HOUR) // MINUTE
    if hours > 0 and minutes > 0:
        return f"{hours} soat {minutes} daqiqa"
    elif hours > 0:
        return f"{hours} soat"
    else:
        return f"{minutes} daqiqa"

def parse_time(time_str: str) -> Optional[int]:
    if not time_str:
        return None
    match = re.match(r'^(\d+)([mh])$', time_str.lower())
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)
    if unit == 'm':
        return value * MINUTE
    elif unit == 'h':
        return value * HOUR
    return None

# ============================================
# BOT FUNKSIYALARI
# ============================================

async def send_message_with_retry(context, chat_id, text, parse_mode=None, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                read_timeout=READ_TIMEOUT,
                write_timeout=WRITE_TIMEOUT,
                connect_timeout=CONNECTION_TIMEOUT,
                pool_timeout=POOL_TIMEOUT
            )
            return True
        except TimedOut:
            if attempt < max_retries - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False
        except:
            return False
    return False

async def send_quote(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Hikmat yuborish - FAQAT IZOHLAR GURUHI BO'LSA CHIQADI"""
    global QUOTES, quote_manager
    
    if not QUOTES:
        QUOTES = load_json_file(QUOTES_FILE, [])
        if not QUOTES:
            return
    
    quote = quote_manager.get_random_quote(chat_id)
    if not quote:
        quote = random.choice(QUOTES)
    
    message = f"""
<b>"{quote['text']}"</b>

<blockquote><b>— {quote['author']}</b></blockquote>
"""
    
    # Inline buttonlar uchun ro'yxat
    buttons = []
    
    # ===== 1. IZOHLAR GURUHI BUTTONI (AGAR MAVJUD BO'LSA) =====
    try:
        chat = await context.bot.get_chat(chat_id)
        
        # Kanal ekanligini tekshirish
        if chat.type == 'channel':
            # Izohlar guruhi bormi tekshirish
            if hasattr(chat, 'linked_chat_id') and chat.linked_chat_id:
                # Izohlar guruhi mavjud
                comments_group_id = chat.linked_chat_id
                
                # Izohlar guruhining ma'lumotini olish
                try:
                    comments_chat = await context.bot.get_chat(comments_group_id)
                    
                    # Izohlar guruhi uchun link yaratish
                    if comments_chat.username:
                        comments_link = f"https://t.me/{comments_chat.username}"
                        comments_text = f"💬 {comments_chat.title}"
                    else:
                        comments_link = f"https://t.me/c/{str(comments_group_id)[4:]}"
                        comments_text = "💬 Izohlar guruhi"
                    
                    # Birinchi qatorga izohlar guruhi buttonini qo'shish
                    buttons.append([InlineKeyboardButton(
                        text=comments_text,
                        url=comments_link
                    )])
                    print(f"✅ Izohlar guruhi topildi: {comments_chat.title}")
                    
                except Exception as e:
                    print(f"❌ Izohlar guruhini olishda xatolik: {e}")
                    # Izohlar guruhi topilmasa, hech narsa qo'shma
                    pass
            else:
                # Izohlar guruhi yo'q - HECH NARSA QO'SHMA
                print(f"ℹ️ Kanalda izohlar guruhi yo'q: {chat.title}")
    except Exception as e:
        print(f"❌ Kanal ma'lumotini olishda xatolik: {e}")
    
    # ===== 2. REKLAMA KANALLARI BUTTONLARI =====
    reklama_buttons = []
    for channel_id, channel in channel_manager.get_channels().items():
        title = channel.get('title', 'Kanal')
        username = channel.get('username')
        
        if username:
            button = InlineKeyboardButton(
                text=f"📢 {title}",
                url=f"https://t.me/{username}"
            )
            reklama_buttons.append([button])
        else:
            chat_id_int = int(channel_id) if channel_id.lstrip('-').isdigit() else None
            if chat_id_int and str(chat_id_int).startswith('-100'):
                private_link = f"https://t.me/c/{str(chat_id_int)[4:]}"
                button = InlineKeyboardButton(
                    text=f"📢 {title}",
                    url=private_link
                )
                reklama_buttons.append([button])
    
    # Reklama buttonlarini random tartibda chiqarish
    random.shuffle(reklama_buttons)
    
    # Ikkala ro'yxatni birlashtirish (izohlar birinchi, keyin reklamalar)
    buttons.extend(reklama_buttons)
    
    # Inline keyboard yaratish
    reply_markup = None
    if buttons:
        reply_markup = InlineKeyboardMarkup(buttons)
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        print(f"✅ Post yuborildi: {chat_id}")
        return True
    except Exception as e:
        print(f"❌ Xatolik {chat_id}: {e}")
        return False

async def quote_scheduler(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Scheduler"""
    print(f"🔄 Scheduler boshlandi: {chat_id}")
    
    while True:
        try:
            settings = chat_settings.get(chat_id)
            if not settings:
                print(f"❌ Scheduler to'xtadi: {chat_id} (settings topilmadi)")
                break
            
            next_run = settings['next_run']
            now = datetime.now()
            
            if isinstance(next_run, str):
                next_run = datetime.fromisoformat(next_run)
                settings['next_run'] = next_run
            
            if now >= next_run:
                print(f"⏰ Hikmat yuborish vaqti: {chat_id}")
                success = await send_quote(context, chat_id)
                
                if success:
                    settings['next_run'] = now + timedelta(seconds=settings['interval'])
                    save_chat_settings()
                    print(f"✅ Keyingi hikmat: {settings['next_run'].strftime('%H:%M:%S')}")
                else:
                    # Xatolik bo'lsa, 5 minutdan keyin qayta urinish
                    settings['next_run'] = now + timedelta(minutes=5)
                    print(f"⚠️ Xatolik, 5 daqiqadan keyin qayta uriniladi")
            
            await asyncio.sleep(30)  # Har 30 sekundda tekshirish
            
        except Exception as e:
            print(f"❌ Scheduler xatolik {chat_id}: {e}")
            await asyncio.sleep(60)

async def start_scheduler_for_chat(application: Application, chat_id: int, interval: int = DEFAULT_INTERVAL):
    """Schedulerni ishga tushirish"""
    if chat_id in chat_settings:
        if 'task' in chat_settings[chat_id]:
            old_task = chat_settings[chat_id]['task']
            if not old_task.done():
                old_task.cancel()
    
    task = asyncio.create_task(quote_scheduler(application, chat_id))
    
    if chat_id in chat_settings:
        current_interval = chat_settings[chat_id].get('interval', interval)
        next_run = chat_settings[chat_id].get('next_run')
        
        if next_run is None:
            next_run = datetime.now() + timedelta(seconds=current_interval)
        elif isinstance(next_run, str):
            next_run = datetime.fromisoformat(next_run)
    else:
        current_interval = interval
        next_run = datetime.now() + timedelta(seconds=interval)
    
    chat_settings[chat_id] = {
        'interval': current_interval,
        'next_run': next_run,
        'task': task
    }
    
    save_chat_settings()
    print(f"✅ Scheduler ishga tushdi: {chat_id} ({current_interval} sek)")

# ============================================
# ASOSIY BUYRUQ - KANALNI TEKSHIRISH VA ISHGA TUSHIRISH
# ============================================

async def check_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /check @kanalnomi - Kanalni tekshirish va ishga tushirish
    Bu buyruq faqat kanal adminlari uchun ishlaydi
    """
    chat = update.effective_chat
    user = update.effective_user
    
    # Faqat shaxsiy xabarlarda ishlaydi
    if chat.type != 'private':
        await send_message_with_retry(
            context, chat.id,
            "❌ Bu buyruq faqat shaxsiy xabarlarda ishlaydi!\n"
            "Botga private chatda yozing: @{}".format(context.bot.username),
            ParseMode.HTML
        )
        return
    
    if not context.args:
        await send_message_with_retry(
            context, chat.id,
            "❌ Iltimos, kanal username ni yozing!\n\n"
            "Misol: <code>/check @kanalnomi</code>\n\n"
            "<i>Botni kanalga admin qilgan bo'lishingiz kerak!</i>",
            ParseMode.HTML
        )
        return
    
    channel_username = context.args[0]
    
    # Kanal username ni tekshirish
    if not channel_username.startswith('@'):
        channel_username = '@' + channel_username
    
    await send_message_with_retry(
        context, chat.id,
        f"🔍 <b>Kanal tekshirilmoqda:</b> {channel_username}\n\n"
        f"<i>Iltimos, kuting...</i>",
        ParseMode.HTML
    )
    
    try:
        # Kanal ma'lumotini olish
        channel = await context.bot.get_chat(channel_username)
        
        # Botning kanaldagi statusini tekshirish
        try:
            bot_member = await context.bot.get_chat_member(channel.id, context.bot.id)
            
            if bot_member.status != 'administrator':
                await send_message_with_retry(
                    context, chat.id,
                    f"❌ <b>Bot kanalda admin emas!</b>\n\n"
                    f"1. Botni kanalga admin qiling: {channel_username}\n"
                    f"2. Quyidagi ruxsatlarni bering:\n"
                    f"   • Xabar yuborish (post messages)\n"
                    f"   • Tahrirlash (edit messages)\n\n"
                    f"<i>So'ng /check {channel_username} ni qayta bosing</i>",
                    ParseMode.HTML
                )
                return
        except Exception as e:
            await send_message_with_retry(
                context, chat.id,
                f"❌ <b>Bot kanalda topilmadi!</b>\n\n"
                f"Botni kanalga admin qiling: {channel_username}",
                ParseMode.HTML
            )
            return
        
        # ===== MUHIM QISM: USER KANAL ADMINI EKANLIGINI TEKSHIRISH =====
        try:
            # Foydalanuvchining kanaldagi statusini tekshirish
            user_member = await context.bot.get_chat_member(channel.id, user.id)
            
            # Adminlikni tekshirish (creator yoki administrator)
            if user_member.status not in ['creator', 'administrator']:
                await send_message_with_retry(
                    context, chat.id,
                    f"❌ <b>Siz bu kanalning admini emassiz!</b>\n\n"
                    f"Kanal: {channel.title}\n"
                    f"Sizning statusingiz: {user_member.status}\n\n"
                    f"<i>Faqat kanal adminlari /check buyrug'idan foydalana oladi!</i>",
                    ParseMode.HTML
                )
                return
                
        except Exception as e:
            # Agar foydalanuvchi kanalda umuman bo'lmasa
            await send_message_with_retry(
                context, chat.id,
                f"❌ <b>Siz bu kanalda topilmadingiz!</b>\n\n"
                f"Kanal: {channel.title}\n\n"
                f"<i>Siz kanal admini bo'lishingiz kerak!</i>",
                ParseMode.HTML
            )
            return
        # ===== TEKSHIRISH TUGADI =====
        
        # Test xabar yuborish
        test_message = f"""
🧪 <b>HUSHXABAR</b>

✅ Bot kanalda admin va xabar yubora oladi!
✅ Siz kanal admini ekanligingiz tasdiqlandi!

📊 <b>Kanal ma'lumotlari:</b>
• Nomi: {channel.title}
• ID: <code>{channel.id}</code>
• Username: {channel_username}
• Sizning status: {user_member.status}

"""
        
        # Izohlar guruhi haqida ma'lumot
        if hasattr(channel, 'linked_chat_id') and channel.linked_chat_id:
            try:
                comments_chat = await context.bot.get_chat(channel.linked_chat_id)
                test_message += f"• Izohlar guruhi: {comments_chat.title} (@{comments_chat.username if comments_chat.username else 'ID'})\n"
            except:
                test_message += f"• Izohlar guruhi: mavjud (ID: {channel.linked_chat_id})\n"
        else:
            test_message += f"• Izohlar guruhi: yo'q\n"
        
        test_message += f"""
⏱ Vaqt: {datetime.now().strftime('%H:%M:%S')}

<i>Hikmatlar avtomatik yuborila boshlaydi...</i>
"""
        
        await context.bot.send_message(
            chat_id=channel.id,
            text=test_message,
            parse_mode=ParseMode.HTML
        )
        
        # Kanalni bot_channels ga qo'shish (added_by = user.id)
        bot_channels.add_channel(channel.id, channel.title, channel.username, user.id)
        
        # Schedulerni ishga tushirish
        if channel.id not in chat_settings:
            await start_scheduler_for_chat(context.application, channel.id)
        
        # Darhol birinchi hikmatni yuborish
        await send_quote(context, channel.id)
        
        await send_message_with_retry(
            context, chat.id,
            f"✅ <b>Kanal muvaffaqiyatli ulandi!</b>\n\n"
            f"📢 <b>Kanal:</b> {channel.title}\n"
            f"🆔 <b>ID:</b> <code>{channel.id}</code>\n"
            f"👑 <b>Sizning status:</b> {user_member.status}\n"
            f"⏱ <b>Vaqt oralig'i:</b> {format_time(DEFAULT_INTERVAL)}\n\n"
            f"📌 Test xabar va birinchi hikmat kanalga yuborildi!\n"
            f"📊 <b>Buyruqlar:</b>\n"
            f"• /time <code>{channel.id}</code> 30m - intervalni o'zgartirish\n"
            f"• /stop <code>{channel.id}</code> - to'xtatish\n"
            f"• /channels - kanallar ro'yxati\n\n"
            f"<i>Eslatma: Bu buyruqlarni shu chatda yozishingiz mumkin</i>",
            ParseMode.HTML
        )
        
    except Exception as e:
        error_text = str(e)
        if "chat not found" in error_text.lower():
            await send_message_with_retry(
                context, chat.id,
                f"❌ <b>Kanal topilmadi!</b>\n\n"
                f"<code>{channel_username}</code> kanali mavjud emas yoki bot qo'shilmagan.",
                ParseMode.HTML
            )
        else:
            await send_message_with_retry(
                context, chat.id,
                f"❌ <b>Xatolik yuz berdi!</b>\n\n<code>{error_text}</code>",
                ParseMode.HTML
            )

# ============================================
# BOSHQA BUYRUQLAR
# ============================================

async def my_channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi ulagan kanallar ro'yxati"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type != 'private':
        await send_message_with_retry(context, chat.id, "❌ Bu buyruq faqat shaxsiy xabarlarda ishlaydi!", ParseMode.HTML)
        return
    
    user_channels = []
    for chat_id, info in bot_channels.get_channels().items():
        if info.get('added_by') == user.id:
            user_channels.append(info)
    
    if not user_channels:
        await send_message_with_retry(
            context, chat.id,
            "📋 <b>Sizning kanallaringiz</b>\n\n"
            "Siz hali hech qanday kanal ulamagansiz.\n"
            "/check @kanalnomi orqali kanal ulashing.",
            ParseMode.HTML
        )
        return
    
    text = "📋 <b>Sizning kanallaringiz</b>\n\n"
    for i, ch in enumerate(user_channels, 1):
        text += f"{i}. <b>{ch['title']}</b>\n"
        text += f"   ID: <code>{ch['id']}</code>\n"
        if ch.get('username'):
            text += f"   @{ch['username']}\n"
        text += "\n"
    
    await send_message_with_retry(context, chat.id, text, ParseMode.HTML)

async def stop_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanalni to'xtatish"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type != 'private':
        await send_message_with_retry(context, chat.id, "❌ Bu buyruq faqat shaxsiy xabarlarda ishlaydi!", ParseMode.HTML)
        return
    
    if not context.args:
        await send_message_with_retry(
            context, chat.id,
            "❌ Kanal ID sini yozing!\n"
            "Misol: /stop -1001234567890\n"
            "Kanallar ro'yxati: /channels",
            ParseMode.HTML
        )
        return
    
    try:
        channel_id = int(context.args[0])
        
        # Kanal mavjudligini tekshirish
        channel_info = bot_channels.get_channels().get(channel_id)
        if not channel_info:
            await send_message_with_retry(
                context, chat.id,
                "❌ Bu kanal botga ulangan kanallar ro'yxatida yo'q!",
                ParseMode.HTML
            )
            return
        
        # ===== MUHIM: KANAL ADMINI EKANLIGINI TEKSHIRISH =====
        try:
            # Foydalanuvchining kanaldagi statusini tekshirish
            user_member = await context.bot.get_chat_member(channel_id, user.id)
            
            # Adminlikni tekshirish (creator yoki administrator)
            if user_member.status not in ['creator', 'administrator']:
                await send_message_with_retry(
                    context, chat.id,
                    f"❌ <b>Bu kanal sizga tegishli emas!</b>\n\n"
                    f"Kanal: {channel_info['title']}\n"
                    f"Sizning statusingiz: {user_member.status}\n\n"
                    f"<i>Faqat kanal adminlari kanalni to'xtata oladi!</i>",
                    ParseMode.HTML
                )
                return
        except Exception as e:
            await send_message_with_retry(
                context, chat.id,
                f"❌ <b>Siz bu kanalda topilmadingiz!</b>\n\n"
                f"Kanal: {channel_info['title']}",
                ParseMode.HTML
            )
            return
        # ===== TEKSHIRISH TUGADI =====
        
        # Schedulerni to'xtatish
        if channel_id in chat_settings and 'task' in chat_settings[channel_id]:
            chat_settings[channel_id]['task'].cancel()
            del chat_settings[channel_id]
            save_chat_settings()
        
        # Kanalni o'chirish
        bot_channels.remove_channel(channel_id)
        
        # Kanalga xabar yuborish (to'xtatilgani haqida)
        try:
            await context.bot.send_message(
                chat_id=channel_id,
                text=f"🛑 <b>Kanal to'xtatildi</b>\n\n"
                     f"Admin @{user.username if user.username else 'User'} tomonidan to'xtatildi.\n"
                     f"Vaqt: {datetime.now().strftime('%H:%M:%S')}",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        await send_message_with_retry(
            context, chat.id,
            f"✅ Kanal to'xtatildi: {channel_info['title']}",
            ParseMode.HTML
        )
        
    except ValueError:
        await send_message_with_retry(
            context, chat.id,
            "❌ Noto'g'ri ID formati!",
            ParseMode.HTML
        )

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal vaqtini o'zgartirish"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type != 'private':
        await send_message_with_retry(context, chat.id, "❌ Bu buyruq faqat shaxsiy xabarlarda ishlaydi!", ParseMode.HTML)
        return
    
    if len(context.args) < 2:
        await send_message_with_retry(
            context, chat.id,
            "❌ Format: /time KANAL_ID vaqt\n"
            "Misol: /time -1001234567890 30m\n"
            "Vaqt: 30m, 1h, 45m",
            ParseMode.HTML
        )
        return
    
    try:
        channel_id = int(context.args[0])
        time_str = context.args[1]
        
        # Kanal mavjudligini tekshirish
        channel_info = bot_channels.get_channels().get(channel_id)
        if not channel_info:
            await send_message_with_retry(
                context, chat.id,
                "❌ Bu kanal botga ulangan kanallar ro'yxatida yo'q!",
                ParseMode.HTML
            )
            return
        
        # ===== MUHIM: KANAL ADMINI EKANLIGINI TEKSHIRISH =====
        try:
            # Foydalanuvchining kanaldagi statusini tekshirish
            user_member = await context.bot.get_chat_member(channel_id, user.id)
            
            # Adminlikni tekshirish (creator yoki administrator)
            if user_member.status not in ['creator', 'administrator']:
                await send_message_with_retry(
                    context, chat.id,
                    f"❌ <b>Bu kanal sizga tegishli emas!</b>\n\n"
                    f"Kanal: {channel_info['title']}\n"
                    f"Sizning statusingiz: {user_member.status}\n\n"
                    f"<i>Faqat kanal adminlari vaqtni o'zgartira oladi!</i>",
                    ParseMode.HTML
                )
                return
        except Exception as e:
            await send_message_with_retry(
                context, chat.id,
                f"❌ <b>Siz bu kanalda topilmadingiz!</b>\n\n"
                f"Kanal: {channel_info['title']}",
                ParseMode.HTML
            )
            return
        # ===== TEKSHIRISH TUGADI =====
        
        seconds = parse_time(time_str)
        if not seconds:
            await send_message_with_retry(
                context, chat.id,
                "❌ Noto'g'ri vaqt formati!\n"
                "Misol: 30m, 1h, 45m",
                ParseMode.HTML
            )
            return
        
        if seconds < MIN_INTERVAL or seconds > MAX_INTERVAL:
            await send_message_with_retry(
                context, chat.id,
                f"❌ Vaqt {format_time(MIN_INTERVAL)} dan {format_time(MAX_INTERVAL)} gacha bo'lishi kerak!",
                ParseMode.HTML
            )
            return
        
        if channel_id in chat_settings:
            old = chat_settings[channel_id]['interval']
            chat_settings[channel_id]['interval'] = seconds
            save_chat_settings()
            
            await send_message_with_retry(
                context, chat.id,
                f"✅ <b>Vaqt o'zgartirildi!</b>\n\n"
                f"📢 Kanal: {channel_info['title']}\n"
                f"⚙️ Eski: {format_time(old)}\n"
                f"⚙️ Yangi: {format_time(seconds)}",
                ParseMode.HTML
            )
        else:
            await send_message_with_retry(
                context, chat.id,
                "❌ Kanal ishga tushmagan!",
                ParseMode.HTML
            )
            
    except ValueError:
        await send_message_with_retry(context, chat.id, "❌ Noto'g'ri ID!", ParseMode.HTML)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i"""
    chat = update.effective_chat
    
    welcome = f"""
👋 <b>Assalomu alaykum!</b>

Men <b>Hikmatlar botiman</b>. Solih zotlardan turli xil hikmatlar yuboraman.

📌 <b>Kanal ulash:</b>
• /check @kanalnomi - o'z kanalingizni ulash

📊 <b>Kanallar:</b>
• /channels - kanallar ro'yxati
• /time KANAL_ID vaqt - vaqtni o'zgartirish
• /stop KANAL_ID - kanalni to'xtatish

📚 <b>Reklama kanallari (adminlar uchun):</b>
• /channel @kanalnomi - reklama kanali qo'shish
• /channellist - reklama kanallari ro'yxati

⚙️ <b>Versiya:</b> {BOT_VERSION}
📚 <b>Hikmatlar:</b> {len(QUOTES)} ta
"""
    
    await send_message_with_retry(context, chat.id, welcome, ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)

# ============================================
# REKLAMA KANALLARI UCHUN (ADMINLAR)
# ============================================

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reklama kanali qo'shish (inline button uchun)"""
    chat = update.effective_chat
    user = update.effective_user
    
    if not admin_manager.is_admin(user.id):
        await send_message_with_retry(
            context, chat.id,
            "❌ Bu buyruq faqat adminlar uchun!",
            ParseMode.HTML
        )
        return
    
    if not context.args:
        await send_message_with_retry(
            context, chat.id,
            "❌ Format: /channel @kanalnomi Kanal nomi",
            ParseMode.HTML
        )
        return
    
    arg = context.args[0]
    channel_name = ' '.join(context.args[1:]) if len(context.args) > 1 else None
    
    if arg.startswith('@'):
        username = arg[1:]
        try:
            chat_info = await context.bot.get_chat(arg)
            chat_id = str(chat_info.id)
            chat_title = channel_name if channel_name else chat_info.title
            chat_username = chat_info.username
            
            channel_manager.add_channel(chat_id, chat_title, chat_username)
            
            await send_message_with_retry(
                context, chat.id,
                f"✅ <b>Reklama kanali qo'shildi!</b>\n\n"
                f"📢 Nomi: <code>{chat_title}</code>\n"
                f"🔗 Link: @{chat_username}\n\n"
                f"<i>Bu kanal hikmatlar ostida chiqadi</i>",
                ParseMode.HTML
            )
        except:
            await send_message_with_retry(
                context, chat.id,
                f"❌ {arg} topilmadi!",
                ParseMode.HTML
            )
    else:
        await send_message_with_retry(
            context, chat.id,
            "❌ Noto'g'ri format! @ bilan boshlanishi kerak",
            ParseMode.HTML
        )

async def channeldel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reklama kanalini o'chirish"""
    chat = update.effective_chat
    user = update.effective_user
    
    if not admin_manager.is_admin(user.id):
        await send_message_with_retry(
            context, chat.id,
            "❌ Bu buyruq faqat adminlar uchun!",
            ParseMode.HTML
        )
        return
    
    if not context.args:
        await send_message_with_retry(
            context, chat.id,
            "❌ Format: /channeldel @kanalnomi",
            ParseMode.HTML
        )
        return
    
    arg = context.args[0]
    
    if arg.startswith('@'):
        username = arg[1:]
        for cid, info in channel_manager.get_channels().items():
            if info.get('username') == username:
                channel_manager.remove_channel(cid)
                await send_message_with_retry(
                    context, chat.id,
                    f"✅ Reklama kanali o'chirildi: @{username}",
                    ParseMode.HTML
                )
                return
        
        await send_message_with_retry(
            context, chat.id,
            f"❌ @{username} topilmadi!",
            ParseMode.HTML
        )
    else:
        await send_message_with_retry(
            context, chat.id,
            "❌ Noto'g'ri format! @ bilan boshlanishi kerak",
            ParseMode.HTML
        )

async def channellist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reklama kanallari ro'yxati"""
    chat = update.effective_chat
    user = update.effective_user
    
    if not admin_manager.is_admin(user.id):
        await send_message_with_retry(
            context, chat.id,
            "❌ Bu buyruq faqat adminlar uchun!",
            ParseMode.HTML
        )
        return
    
    channels = channel_manager.get_channels()
    
    if not channels:
        message = "📋 <b>REKLAMA KANALLARI</b>\n\nKanallar mavjud emas."
    else:
        text = ""
        for i, (chat_id, info) in enumerate(channels.items(), 1):
            title = info.get('title', 'Noma\'lum')
            username = info.get('username')
            username_text = f"@{username}" if username else "Link yo'q"
            text += f"{i}. <b>{title}</b>\n   {username_text}\n\n"
        
        message = f"📋 <b>REKLAMA KANALLARI</b>\n\n{text}Jami: {len(channels)} ta"
    
    await send_message_with_retry(context, chat.id, message, ParseMode.HTML)

# ============================================
# YANGI A'ZOLAR HANDLERI
# ============================================

async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi guruh/kanalga qo'shilganda"""
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat = update.effective_chat
            
            # Schedulerni ishga tushirish
            await start_scheduler_for_chat(context.application, chat.id)
            
            # Agar kanal bo'lsa, bot_channels ga qo'shish
            if chat.type == 'channel':
                bot_channels.add_channel(chat.id, chat.title, chat.username, added_by=0)  # 0 = avtomatik
                print(f"✅ Kanal avtomatik qo'shildi: {chat.id} - {chat.title}")
            
            welcome = f"""
🤖 <b>Hikmatlar {'kanal' if chat.type == 'channel' else 'guruh'}ga qo'shildi!</b>

📊 <b>Ma'lumot:</b>
• Vaqt oralig'i: <code>{format_time(DEFAULT_INTERVAL)}</code>
• Hikmatlar soni: <code>{len(QUOTES)}</code> ta
• Versiya: <code>{BOT_VERSION}</code>

✨ <i>Hikmatlar avtomatik yuborila boshlaydi!</i>

📌 <b>Eslatma:</b> Agar bu kanal bo'lsa, botga shaxsiy xabarda 
<code>/check {chat.username if chat.username else 'KANAL_ID'}</code> 
yozib kanalni boshqarishingiz mumkin.
"""
            
            await send_message_with_retry(context, chat.id, welcome, ParseMode.HTML)

# ============================================
# TEST BUYRUQLARI
# ============================================

async def test_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kanal ma'lumotlarini tekshirish"""
    chat = update.effective_chat
    user = update.effective_user
    
    if not admin_manager.is_admin(user.id):
        await send_message_with_retry(context, chat.id, "❌ Admin emassiz!", ParseMode.HTML)
        return
    
    if not context.args:
        await send_message_with_retry(
            context, chat.id,
            "❌ /testchannel @kanalnomi",
            ParseMode.HTML
        )
        return
    
    try:
        channel = await context.bot.get_chat(context.args[0])
        
        info = f"""
📊 <b>KANAL MA'LUMOTLARI</b>

📌 Nomi: {channel.title}
🆔 ID: <code>{channel.id}</code>
🔗 Username: @{channel.username if channel.username else 'yo\'q'}
📋 Turi: {channel.type}

<b>Izohlar guruhi:</b>
"""
        
        # Izohlar guruhi bormi tekshirish
        if hasattr(channel, 'linked_chat_id') and channel.linked_chat_id:
            try:
                comments = await context.bot.get_chat(channel.linked_chat_id)
                info += f"✅ MAVJUD\n"
                info += f"   Nomi: {comments.title}\n"
                info += f"   ID: <code>{comments.id}</code>\n"
                if comments.username:
                    info += f"   @{comments.username}\n"
            except:
                info += f"❌ Xatolik: izohlar guruhi topilmadi\n"
        else:
            info += f"❌ IZOHLAR GURUHI YO'Q\n"
        
        await send_message_with_retry(context, chat.id, info, ParseMode.HTML)
        
    except Exception as e:
        await send_message_with_retry(
            context, chat.id,
            f"❌ Xatolik: {e}",
            ParseMode.HTML
        )

# ============================================
# BOTNI ISHGA TUSHIRISH
# ============================================

async def post_init(application: Application):
    """Bot ishga tushganda"""
    print("=" * 60)
    print("🔄 Bot ishga tushmoqda...")
    
    # Avval saqlangan chat_settings dan schedulerlarni ishga tushirish
    for chat_id in list(chat_settings.keys()):
        try:
            await start_scheduler_for_chat(application, chat_id)
            print(f"  ✅ Chat {chat_id} ishga tushirildi")
        except Exception as e:
            print(f"  ❌ Chat {chat_id} xatolik: {e}")
    
    print("=" * 60)

def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(CONNECTION_TIMEOUT)
        .read_timeout(READ_TIMEOUT)
        .write_timeout(WRITE_TIMEOUT)
        .pool_timeout(POOL_TIMEOUT)
        .post_init(post_init)
        .build()
    )
    
    # Asosiy buyruqlar
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Kanal ulash buyruqlari
    application.add_handler(CommandHandler("check", check_channel_command))
    application.add_handler(CommandHandler("channels", my_channels_command))
    application.add_handler(CommandHandler("stop", stop_channel_command))
    application.add_handler(CommandHandler("time", time_command))
    
    # Reklama kanallari (faqat adminlar)
    application.add_handler(CommandHandler("channel", channel_command))
    application.add_handler(CommandHandler("channeldel", channeldel_command))
    application.add_handler(CommandHandler("channellist", channellist_command))
    
    # Test buyruqlari
    application.add_handler(CommandHandler("testchannel", test_channel_info))
    
    # Yangi a'zolar
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, 
        handle_new_chat_members
    ))
    
    print("=" * 60)
    print(f"🤖 {BOT_NAME} ishga tushmoqda...")
    print(f"📦 Versiya: {BOT_VERSION}")
    print(f"👑 Superadmin: {admin_manager.super_admin}")
    print(f"👥 Adminlar: {len(admin_manager.get_admins_list())} ta")
    print(f"📢 Reklama kanallari: {len(channel_manager.get_channels())} ta")
    print(f"📢 Bot kanallari: {len(bot_channels.get_channels())} ta")
    print(f"⏱ Standart vaqt: {format_time(DEFAULT_INTERVAL)}")
    print(f"📚 Hikmatlar: {len(QUOTES)} ta")
    print("=" * 60)
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        timeout=POLLING_TIMEOUT,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()