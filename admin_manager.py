import json
import os
from typing import Dict, List, Optional, Set

# Fayl yo'llari
ADMINS_FILE = "admins.json"
CHANNELS_FILE = "channels.json"

class AdminManager:
    """Adminlarni boshqarish uchun klass"""
    
    def __init__(self):
        self.super_admin = 5600602320  # SUPERADMIN ID (o'zingizning ID'ingizni yozing)
        self.admins: Set[int] = self._load_admins()
        print(f"👑 Superadmin: {self.super_admin}")
        print(f"👥 Adminlar: {len(self.admins)} ta")
    
    def _load_admins(self) -> Set[int]:
        """Adminlarni fayldan yuklash"""
        try:
            if os.path.exists(ADMINS_FILE):
                with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('admins', []))
            return set()
        except Exception as e:
            print(f"❌ Adminlarni yuklashda xatolik: {e}")
            return set()
    
    def _save_admins(self):
        """Adminlarni faylga saqlash"""
        try:
            with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'admins': list(self.admins)}, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"❌ Adminlarni saqlashda xatolik: {e}")
            return False
    
    def is_superadmin(self, user_id: int) -> bool:
        """Superadmin ekanligini tekshirish"""
        return user_id == self.super_admin
    
    def is_admin(self, user_id: int) -> bool:
        """Admin ekanligini tekshirish"""
        return user_id in self.admins or self.is_superadmin(user_id)
    
    def add_admin(self, user_id: int) -> bool:
        """Yangi admin qo'shish"""
        if user_id == self.super_admin:
            return False  # Superadminni qayta qo'shib bo'lmaydi
        self.admins.add(user_id)
        return self._save_admins()
    
    def remove_admin(self, user_id: int) -> bool:
        """Adminni o'chirish"""
        if user_id == self.super_admin:
            return False  # Superadminni o'chirib bo'lmaydi
        if user_id in self.admins:
            self.admins.remove(user_id)
            return self._save_admins()
        return False
    
    def get_admins_list(self) -> List[int]:
        """Adminlar ro'yxatini olish"""
        return list(self.admins)

class ChannelManager:
    """Kanallar va guruhlarni boshqarish uchun klass"""
    
    def __init__(self):
        self.channels: Dict[str, dict] = self._load_channels()
        print(f"📢 Kanallar: {len(self.channels)} ta")
    
    def _load_channels(self) -> Dict[str, dict]:
        """Kanallarni fayldan yuklash"""
        try:
            if os.path.exists(CHANNELS_FILE):
                with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Kanallarni yuklashda xatolik: {e}")
            return {}
    
    def _save_channels(self) -> bool:
        """Kanallarni faylga saqlash"""
        try:
            with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.channels, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"❌ Kanallarni saqlashda xatolik: {e}")
            return False
    
    def add_channel(self, chat_id: str, title: str, username: str = None, chat_type: str = "channel"):
        """Kanal yoki guruh qo'shish"""
        self.channels[chat_id] = {
            'id': chat_id,
            'title': title,
            'username': username,
            'type': chat_type,
            'added_at': str(datetime.now())
        }
        return self._save_channels()
    
    def remove_channel(self, chat_id: str) -> bool:
        """Kanal yoki guruhni o'chirish"""
        if chat_id in self.channels:
            del self.channels[chat_id]
            return self._save_channels()
        return False
    
    def get_channels(self) -> Dict[str, dict]:
        """Barcha kanallar ro'yxati"""
        return self.channels
    
    def get_channel_link(self, chat_id: str) -> Optional[str]:
        """Kanal linkini olish"""
        channel = self.channels.get(chat_id)
        if channel:
            if channel.get('username'):
                return f"https://t.me/{channel['username']}"
            else:
                # Raqamli ID bo'lsa
                chat_id_int = int(chat_id) if chat_id.lstrip('-').isdigit() else None
                if chat_id_int and str(chat_id_int).startswith('-100'):
                    return f"https://t.me/c/{str(chat_id_int)[4:]}"
        return None
    
    def format_inline_buttons(self) -> List:
        """Inline buttonlar uchun kanallar ro'yxati"""
        buttons = []
        for chat_id, channel in self.channels.items():
            link = self.get_channel_link(chat_id)
            if link:
                buttons.append([{
                    'text': f"📢 {channel['title']}",
                    'url': link
                }])
        return buttons

# Global obyektlar
admin_manager = AdminManager()
channel_manager = ChannelManager()

from datetime import datetime