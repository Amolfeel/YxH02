import asyncio
import os
from pyrogram import Client, filters
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from telegraph import Telegraph

from . import YxH, get_anime_character
from YxH.Database.characters import get_all as get_all_anime_characters


# ======================================================
#                   TELEGRAPH SYSTEM
# ======================================================

telegraph_clients = {}  # user.id -> Telegraph instance


async def get_telegraph_client(user):
    if user.id in telegraph_clients:
        return telegraph_clients[user.id]

    tg = Telegraph()
    await asyncio.to_thread(tg.create_account, short_name=user.first_name)

    telegraph_clients[user.id] = tg
    return tg


# ======================================================
#           CREATE TELEGRAPH PAGE FOR EXTRAS
# ======================================================

async def create_telegraph_for_duplicates(user, duplicates: dict):
    tg = await get_telegraph_client(user)

    content = []

    # Sort by most duplicates first
    for char_id, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
        char = await get_anime_character(str(char_id))
        if not char:
            continue

        text = f"• {char.name} (ID: {char.id}) × {count}"
        content.append({
            "tag": "p",
            "children": [text]
        })

    if not content:
        content.append({
            "tag": "p",
            "children": ["No duplicate characters found."]
        })

    page = await asyncio.to_thread(
        tg.create_page,
        title=f"{user.first_name}'s Extra Characters",
        content=content
    )

    return "https://telegra.ph/" + page["path"]


# ======================================================
#            PDF FOR UNCOLLECTED CHARACTERS
# ======================================================

async def create_pdf_for_uncollected(user, uncollected, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"{user.first_name}'s Uncollected Characters")
    y -= 30

    c.setFont("Helvetica", 12)

    if not uncollected:
        c.drawString(50, y, "🎉 You have collected all characters!")
    else:
        for char in uncollected:
            if not char:
                continue

            line = f"{char.name} (ID: {char.id})"

            if y < 50:
                c.showPage()
                y = height - 50

            c.drawString(50, y, line)
            y -= 20

    c.save()


# ======================================================
#                 /extras COMMAND
# ======================================================

@Client.on_message(filters.command("extras"))
@YxH()
async def extras_command(_, m, u):
    user = m.from_user
    coll_dict: dict = u.collection or {}

    if not coll_dict:
        return await m.reply("Your collection is empty.")

    duplicates = {}

    for k, v in coll_dict.items():
        count = 0

        # Case 1: stored as integer count
        if isinstance(v, int):
            count = v

        # Case 2: stored as list/tuple
        elif isinstance(v, (list, tuple, set)):
            count = len(v)

        # Case 3: stored as dict
        elif isinstance(v, dict):
            if "count" in v:
                count = int(v.get("count", 0))
            elif "copies" in v:
                count = int(v.get("copies", 0))
            elif "amount" in v:
                count = int(v.get("amount", 0))

        if count > 1:
            duplicates[str(k)] = count

    if not duplicates:
        return await m.reply("No extras 🆔 found in your collection.")

    msg = await m.reply("📄 Creating your extras list...")

    url = await create_telegraph_for_duplicates(user, duplicates)

    await msg.edit(
        f"📄 **Your Extra Characters List is Ready!**\n\n"
        f"🔗 {url}"
    )


# ======================================================
#               /uncollected COMMAND
# ======================================================

@Client.on_message(filters.command("uncollected"))
@YxH()
async def uncollected_characters(_, m, u):
    user = m.from_user
    coll_dict: dict = u.collection or {}

    all_characters = await get_all_anime_characters()
    if not all_characters:
        return await m.reply("No characters exist in the database.")

    # Fix ID type mismatch
    collected_ids = set(str(k) for k in coll_dict.keys())

    uncollected = [
        char for char in all_characters.values()
        if str(char.id) not in collected_ids
    ]

    if not uncollected:
        return await m.reply("🎉 You have collected all characters!")

    file_path = f"/tmp/{user.id}_uncollected.pdf"
    await create_pdf_for_uncollected(user, uncollected, file_path)

    try:
        await m.reply_document(
            file_path,
            caption=f"📄 You are missing {len(uncollected)} characters."
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
