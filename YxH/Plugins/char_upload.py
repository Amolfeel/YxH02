from pyrogram import Client, filters
from . import YxH
from ..Class.character import AnimeCharacter, YaoiYuriCharacter
from config import ANIME_CHAR_CHANNEL_ID
import asyncio

# ---------------------- PROCESS ONE MESSAGE ----------------------

async def process_message(client: Client, m):
    if not m or not m.photo or not m.caption:
        return "SKIP"

    if m.chat.id != ANIME_CHAR_CHANNEL_ID:
        return "SKIP"

    try:
        spl = m.caption.split(";")
        if len(spl) < 4:
            return f"BAD_CAPTION:{m.id}"

        name = spl[0].strip()
        anime = spl[1].strip()
        rarity = spl[2].strip()
        char_id = int(spl[3].strip())

        # Store Telegram reference instead of external URL
        image_ref = {
            "chat_id": m.chat.id,
            "message_id": m.id
        }

        c = AnimeCharacter(
            char_id,
            image_ref,
            name,
            anime,
            rarity
        )

        # IMPORTANT: pass client so inline file_id can be generated
        await c.add(client)

        return "OK"

    except Exception as e:
        return f"ERROR:{m.id}:{e}"

# ---------------------- COMMAND ----------------------

@Client.on_message(filters.command("aupl"))
@YxH(sudo=True)
async def aupl(client: Client, m, u):
    ok = await m.reply("⚙️ Starting processing...")

    spl = m.text.split()

    if len(spl) == 3:
        st = int(spl[1])
        end = int(spl[2]) + 1
    elif len(spl) == 2:
        st = int(spl[1])
        end = st + 1
    else:
        return await m.reply("**Usage:** `/aupl start end` or `/aupl msg_id`")

    # Split into batches of 200 (Telegram API limit)
    batches = []
    while end - st > 200:
        batches.append(list(range(st, st + 200)))
        st += 200

    if end - st > 0:
        batches.append(list(range(st, end)))

    total = len(batches)
    success = 0
    failed = 0
    skipped = 0

    for index, batch in enumerate(batches, start=1):
        await ok.edit(f"⚙️ Processing batch {index}/{total}...")

        messages = await client.get_messages(ANIME_CHAR_CHANNEL_ID, batch)

        tasks = [process_message(client, msg) for msg in messages]
        results = await asyncio.gather(*tasks)

        for r in results:
            if r == "OK":
                success += 1
            elif r == "SKIP":
                skipped += 1
            else:
                failed += 1
                print("AUPL ERROR:", r)

    await ok.edit(
        f"✅ **Processing Complete**\n\n"
        f"✔️ Success: `{success}`\n"
        f"⚠️ Skipped: `{skipped}`\n"
        f"❌ Failed: `{failed}`"
    )
