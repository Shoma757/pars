from telethon import TelegramClient
import aiohttp
import asyncio
import sqlite3
from datetime import datetime

class TGParser:
    def __init__(self, api_id, api_hash, session_name, db_path, webhook_url, proxy_ip=None, proxy_port=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.db_path = db_path
        self.webhook_url = webhook_url
        self.client = None
        
    if proxy_ip and proxy_port:
            self.proxy = (proxy_ip, int(proxy_port), 'socks5')
        else:
            self.proxy = None

    async def _connect(self):
        if not self.client:
            self.client = TelegramClient(
                self.session_name, 
                self.api_id, 
                self.api_hash,
                
                timeout=30,  
                proxy=self.proxy
            )
            await self.client.connect()
        return self.client

    async def _get_last_id(self, channel):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS messages (channel TEXT, msg_id INTEGER, PRIMARY KEY(channel, msg_id))")
        c.execute("SELECT MAX(msg_id) FROM messages WHERE channel=?", (channel,))
        last = c.fetchone()[0]
        conn.close()
        return last or 0

    async def _save_msg_id(self, channel, msg_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO messages (channel, msg_id) VALUES (?, ?)", (channel, msg_id))
        conn.commit()
        conn.close()

    async def _send_to_webhook(self, data):
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json=data)

    async def run(self, channels):
        client = await self._connect()
        for ch in channels:
            try:
                print(f"🔍 Checking {ch}")
                entity = await client.get_entity(ch)
                last_id = await self._get_last_id(ch)
                async for msg in client.iter_messages(entity, limit=20):
                    if msg.id <= last_id:
                        break
                    await self._send_to_webhook({
                        "channel": ch,
                        "id": msg.id,
                        "date": str(msg.date),
                        "text": msg.text or "",
                        "has_media": bool(msg.media)
                    })
                    await self._save_msg_id(ch, msg.id)
            except Exception as e:
                print(f"❌ Error in {ch}: {e}")
        await client.disconnect()
