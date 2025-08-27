import logging
import logging.config
from datetime import date, datetime
from typing import Union, Optional

import pytz
from aiohttp import web
from pyrogram import Client, __version__, types
from pyrogram.raw.all import layer

from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, PORT, SUPPORT_CHAT_ID
from plugins import web_server
from Script import script
from utils import temp


# Initialize logging from config
try:
    logging.config.fileConfig('logging.conf')
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.error(f"Failed to load logging configuration: {e}")

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        try:
            # Load banned users and chats
            temp.BANNED_USERS, temp.BANNED_CHATS = await db.get_banned()

            # Start bot
            await super().start()

            # Ensure MongoDB indexes
            await Media.ensure_indexes()

            # Fetch bot info
            me = await self.get_me()
            temp.ME = me.id
            temp.U_NAME = me.username
            temp.B_NAME = me.first_name
            self.username = f"@{me.username}"

            # Log startup
            logging.info(f"{me.first_name} running Pyrogram v{__version__} (Layer {layer}) at {me.username}")
            logging.info(LOG_STR)
            logging.info(script.LOGO)

            # Send startup messages
            today = date.today()
            now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%H:%M:%S %p")

            await self.send_message(LOG_CHANNEL, script.RESTART_TXT.format(today, now))
            await self.send_message(SUPPORT_CHAT_ID, script.RESTART_GC_TXT.format(today, now))

            # Start web server
            app_runner = web.AppRunner(await web_server())
            await app_runner.setup()
            await web.TCPSite(app_runner, "0.0.0.0", PORT).start()

        except Exception as e:
            logging.error(f"Bot failed to start: {e}")
            await self.stop()

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")


# Run the bot
if __name__ == "__main__":
    app = Bot()
    app.run()

