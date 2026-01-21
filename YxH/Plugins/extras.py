import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as ikm, InlineKeyboardButton as ikb
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from . import YxH, get_anime_character
from telegraph import Telegraph
from YxH.Database.characters import get_all as get_all_anime_characters


# ======================================================
#                 TELEGRAPH SETUP
# ======================================================

telegraph = Telegraph()
telegraph_accounts = {}  # user.id -> created or not


async def get_telegraph_account(user):
    if user.id in telegraph_accounts:
        return True

    await asyncio.to_thread(
        telegraph.create_account,
        short_name=user.first_name
    )
    telegraph_accounts[user.id] = True
    return True


# ======================================================
#        CREATE TELEGRAPH PAGE FOR DUPLICATES
# ======================================================

async def create_telegraph_for_duplicates(user, duplicates):
    await get_telegraph_account(user)

    html = f"<h3>{user.first_name}'s Duplicate Characters</h3><ul>"

    for dup_id, count in duplicates.items():
        char = await get_anime_character(dup_id)
        if not char:
            continue
        html += f"<li>{char.name} (ID: {char.id}) × {count}</li>"

    html += "</ul>"

    page = await asyncio.to_thread(
        telegraph.create_page,
        title=f"{user.first_name}'s Extra Characters",
        html_content=html
    )

    return page["url"]


# ======================================================
#                 /extras COMMAND
# ======================================================

@Client.on_message(filters.command('extras'))
@YxH()
async def find_duplicates(_, m, u):
    user = m.from_user
    coll_dict: dict = u.collection

    if not coll_dict:
        return await m.reply('Your collection is empty.')

    # ✅ EXACT SAME LOGIC AS YOUR OLD WORKING SCRIPT
    duplicates = {
        k: v for k, v in coll_dict.items()
        if isinstance(v, int) and v > 1
    }

    if not duplicates:
        return await m.reply('No extras 🆔 found in your collection.')

    msg = await m.reply("📄 Creating your extras list...")

    url = await create_telegraph_for_duplicates(user, duplicates)

    await msg.edit(
        f"📄 **Here is your Duplicate Characters list:**\n\n"
        f"🔗 {url}"
    )


# ======================================================
#        TELEGRAPH PAGE FOR UNCOLLECTED (UNCHANGED)
# ======================================================

async def create_telegraph_page_for_uncollected(user, uncollected):
    await get_telegraph_account(user)

    content = f"<strong>{user.first_name}'s Uncollected Characters:</strong><ul>"
    for char in uncollected:
        if not char:
            continue
        content += f"<li>{char.name} (ID: {char.id})</li>"
    content += "</ul>"

    page = await asyncio.to_thread(
        telegraph.create_page,
        title=f"{user.first_name}'s Uncollected Characters",
        html_content=content
    )

    return page["url"]


# ======================================================
#                 /uncollected COMMAND
# ======================================================

@Client.on_message(filters.command('uncollected'))
@YxH()
async def uncollected_characters(_, m, u):
    user = m.from_user
    coll_dict: dict = u.collection or {}

    all_characters = await get_all_anime_characters()
    if not all_characters:
        return await m.reply("No characters exist in the database.")

    collected_ids = set(str(k) for k in coll_dict.keys())

    uncollected = [
        char for char in all_characters.values()
        if str(char.id) not in collected_ids
    ]

    if not uncollected:
        return await m.reply("🎉 You have collected all characters!")

    url = await create_telegraph_page_for_uncollected(user, uncollected)

    await m.reply(
        f"📄 **Your Uncollected Characters List:**\n\n"
        f"🔗 {url}"
    )
