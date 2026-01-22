import pickle
import random
from YxH.Database import db
from pyrogram.types import InlineQueryResultPhoto as iqrp
from ..Utils.templates import inline_template
from pyrogram.types import InlineKeyboardButton as ikb, InlineKeyboardMarkup as ikm

class AnimeCharacter:
    def __init__(self, id, image, name, anime, rarity, price=0):
        self.id = id
        self.image = image  # str (old URL) or dict {"chat_id":..., "message_id":...}
        self.name = name
        self.anime = anime
        self.rarity = rarity
        if price == 0:
            self.price = random.choice(list(range(30000, 60001)))
        else:
            self.price = price

        self._cached_file_id = None

    # ------------------ SEND IMAGE ------------------

    async def send_image(self, client, chat_id):
        if isinstance(self.image, dict):
            await client.copy_message(
                chat_id,
                self.image["chat_id"],
                self.image["message_id"]
            )
        else:
            await client.send_photo(chat_id, self.image)

    # ------------------ GET FILE_ID FOR INLINE ------------------

    async def get_file_id(self, client):
        if self._cached_file_id:
            return self._cached_file_id

        # Old URL system
        if isinstance(self.image, str):
            self._cached_file_id = self.image
            return self._cached_file_id

        # Telegram stored image
        msg = await client.get_messages(
            self.image["chat_id"],
            self.image["message_id"]
        )

        if not msg or not msg.photo:
            raise Exception("Failed to fetch photo from storage channel")

        self._cached_file_id = msg.photo.file_id
        return self._cached_file_id

    # ------------------ ADD TO DATABASE ------------------

    async def add(self, client):
        mk = ikm([[ikb("How many I have❓", callback_data=f"howmany{self.id}")]])

        photo = self.image

        # If Telegram ref → convert to file_id for inline
        if isinstance(self.image, dict):
            photo = await self.get_file_id(client)

        inline = iqrp(
            photo_url=photo,
            thumb_url=photo,
            caption=inline_template(self),
            reply_markup=mk
        )

        self.inline = inline

        await db.anime_characters.update_one(
            {'id': self.id},
            {'$set': {'info': pickle.dumps(self)}},
            upsert=True
        )
    
class YaoiYuriCharacter:
  def __init__(self, id, image, name, price=0):
    self.id = id
    self.image = image
    self.name = name
    if price == 0:
      self.price = random.choice(list(range(30000, 60001)))
    else:
      self.price = price

  async def add(self):
    await db.yaoiyuri_characters.update_one(
      {'id': self.id},
      {'$set': {'info': pickle.dumps(self)}},
      upsert=True
    )
