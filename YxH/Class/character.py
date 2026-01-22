import pickle
import random
from YxH.Database import db
from pyrogram.types import InlineQueryResultPhoto as iqrp
from ..Utils.templates import inline_template
from pyrogram.types import InlineKeyboardButton as ikb, InlineKeyboardMarkup as ikm

class AnimeCharacter:
    def __init__(self, id, image, name, anime, rarity, price=0):
        self.id = id
        self.image = image  # can be URL (str) or Telegram ref (dict)
        self.name = name
        self.anime = anime
        self.rarity = rarity
        if price == 0:
            self.price = random.choice(list(range(30000, 60001)))
        else:
            self.price = price

        # This will be used for inline mode caching
        self._cached_file_id = None

    # ------------------ SEND IMAGE ------------------

    async def send_image(self, client, chat_id):
        if isinstance(self.image, dict):
            # Telegram stored image
            await client.copy_message(
                chat_id,
                self.image["chat_id"],
                self.image["message_id"]
            )
        else:
            # Old URL system
            await client.send_photo(chat_id, self.image)

    # ------------------ GET FILE_ID FOR INLINE ------------------

    async def get_file_id(self, client):
        if self._cached_file_id:
            return self._cached_file_id

        # If old URL system
        if isinstance(self.image, str):
            self._cached_file_id = self.image
            return self._cached_file_id

        # If Telegram stored image → upload once to get file_id
        msg = await client.copy_message(
            "me",
            self.image["chat_id"],
            self.image["message_id"]
        )

        # Extract file_id
        self._cached_file_id = msg.photo.file_id
        return self._cached_file_id

    # ------------------ ADD TO DATABASE ------------------

    async def add(self, client=None):
        mk = ikm([[ikb("How many I have❓", callback_data=f"howmany{self.id}")]])

        # Prepare photo for inline
        photo = self.image

        # If Telegram reference → must convert to file_id
        if isinstance(self.image, dict):
            if not client:
                raise Exception("Client required to add Telegram-stored images")

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
