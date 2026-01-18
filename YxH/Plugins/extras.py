import asyncio
import os
from pyrogram import Client, filters
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from . import YxH, get_anime_character
from YxH.Database.characters import get_all as get_all_anime_characters


# ------------------- PDF Creation for Duplicates -------------------
async def create_pdf_for_duplicates(user, duplicates, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"{user.first_name}'s Duplicate Characters")
    y -= 30

    c.setFont("Helvetica", 12)

    for dup_id, count in duplicates.items():
        char = await get_anime_character(str(dup_id))
        if not char:
            continue

        line = f"{char.name} (ID: {char.id}) × {count}"

        if y < 50:
            c.showPage()
            y = height - 50

        c.drawString(50, y, line)
        y -= 20

    c.save()


# ------------------- PDF Creation for Uncollected -------------------
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


# ------------------- /extras Command -------------------
@Client.on_message(filters.command("extras"))
@YxH()
async def find_duplicates(_, m, u):
    user = m.from_user
    coll_dict: dict = u.collection or {}

    if not coll_dict:
        return await m.reply("Your collection is empty.")

    # Find characters with more than 1 copy
    duplicates = {
        str(k): v for k, v in coll_dict.items()
        if isinstance(v, int) and v > 1
    }

    if not duplicates:
        return await m.reply("No extras 🆔 found in your collection.")

    file_path = f"/tmp/{user.id}_duplicates.pdf"
    await create_pdf_for_duplicates(user, duplicates, file_path)

    try:
        await m.reply_document(
            file_path,
            caption="📄 Here is your Duplicate Characters list."
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ------------------- /uncollected Command -------------------
@Client.on_message(filters.command("uncollected"))
@YxH()
async def uncollected_characters(_, m, u):
    user = m.from_user
    coll_dict: dict = u.collection or {}

    all_characters = await get_all_anime_characters()
    if not all_characters:
        return await m.reply("No characters exist in the database.")

    # 🔥 Fix ID type mismatch bug
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
