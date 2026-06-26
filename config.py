import os
from typing import Dict, Any

# ============================================
# ASOSIY SOZLAMALAR
# ============================================

# Bot tokeni
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8799411473:AAHkeJi9QQnK-8fvjOm8RYkLxrbKHq4DEvc")

# Bot ma'lumotlari
BOT_NAME = "Hikmatlar"
BOT_VERSION = "1.0.0"
BOT_AUTHOR = "@DorulHikmah"

# ============================================
# TIMEOUT SOZLAMALARI (YANGI QO'SHILDI)
# ============================================

# Telegram API so'rovlari uchun timeout (sekundlarda)
REQUEST_TIMEOUT = 30  # 30 sekund
CONNECTION_TIMEOUT = 30  # 30 sekund
POLLING_TIMEOUT = 30  # 30 sekund
READ_TIMEOUT = 30  # 30 sekund
WRITE_TIMEOUT = 30  # 30 sekund
POOL_TIMEOUT = 30  # 30 sekund

# Qayta urinish sozlamalari
MAX_RETRIES = 3  # Maksimal qayta urinishlar soni
RETRY_DELAY = 5  # Qayta urinishlar orasidagi kutish vaqti (sekund)

# ============================================
# VAQT SOZLAMALARI
# ============================================

# Vaqt konstantalari (sekundlarda)
MINUTE = 60
HOUR = 3600
DAY = 86400

# Standart vaqt oralig'i (30 daqiqa)
DEFAULT_INTERVAL = MINUTE * 1  # 1800 sekund

# Minimal va maksimal chegaralar
MIN_INTERVAL = MINUTE  # 1 minut
MAX_INTERVAL = DAY     # 24 soat

# ============================================
# JSON FAYL YO'LLARI
# ============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUOTES_FILE = os.path.join(BASE_DIR, "quotes.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# ============================================
# XABAR MATNLARI
# ============================================

HELP_MESSAGE = """
🤖 <b>FOYDALANISH UCHUN QO\'LLANMA:</b>

Bu bot guruhda Solih zotlar hikmatlarini ma'lum vaqt oralig'ida yuborib turadi.

📌 <b>Buyruqlar:</b>

• <code>/time</code> - Hozirgi vaqtni ko'rish
• <code>/time 30m</code> - 30 daqiqaga sozlash
• <code>/time 1h</code> - 1 soatga sozlash
• <code>/time 90m</code> - 1 soat 30 daqiqa

⚡️ <b>Muhim:</b>
<i>Buyruqlar faqat adminlar uchun!</i>

📊 <b>Chegaralar:</b>
• Minimal: <code>1 minut</code>
• Maksimal: <code>24 soat</code>
"""

START_MESSAGE = """
✅ <b>Bot ishga tushdi!</b>

📊 <b>Ma'lumot:</b>
• Vaqt oralig'i: <code>{interval}</code>
• Hikmatlar soni: <code>{quotes_count}</code>
• Versiya: <code>{version}</code>

📚 <b>Yordam:</b> /help
"""

ERROR_MESSAGES = {
    "not_admin": "❌ <b>Xatolik!</b>\n\nSiz admin emassiz! Bu buyruq faqat guruh adminlari uchun.",
    "invalid_format": "❌ <b>Noto'g'ri format!</b>\n\nMisol: <code>/time 30m</code> yoki <code>/time 1h</code>",
    "time_too_small": f"❌ <b>Vaqt juda kichik!</b>\n\nMinimal: <code>1 minut</code>",
    "time_too_large": f"❌ <b>Vaqt juda katta!</b>\n\nMaksimal: <code>24 soat</code>",
    "not_group": "❌ <b>Xatolik!</b>\n\nBu buyruq faqat guruhlarda ishlaydi!",
    "no_quotes": "❌ <b>Hikmatlar topilmadi!</b>\n\nIltimos, quotes.json faylini tekshiring.",
    "timeout": "⚠️ <b>Ulanish vaqti tugadi!</b>\n\nQayta urinib ko'ring."
}

TIME_MESSAGE = """
⏱ <b>VAQT SOZLAMALARI</b>

📊 <b>Joriy interval:</b>
└─ <code>{current}</code>

⏰ <b>Keyingi hikmat:</b>
└─ <code>{next_time}</code>

⌛️ <b>Qolgan vaqt:</b>
└─ <code>{remaining}</code>

📚 <b>Hikmatlar soni:</b>
└─ <code>{quotes_count}</code>

🔄 <b>O'zgartirish:</b>
<code>/time {example}</code>
"""

QUOTE_MESSAGE = """

<b>"{text}"</b>

<blockquote><b>— {author}</b></blockquote>

⏱ <i>Keyingi hikmat: {next_time}</i>
"""

SUCCESS_MESSAGE = """
✅ <b>Sozlamalar yangilandi!</b>

⚙️ <b>Eski:</b> <code>{old}</code>
⚙️ <b>Yangi:</b> <code>{new}</code>

⏱ <i>Keyingi hikmat {new} dan so'ng</i>
"""