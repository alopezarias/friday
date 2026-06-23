import asyncio
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from openai_codex import AsyncCodex, LocalImageInput
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
MODEL = os.environ.get("MODEL", "gpt-5.4")
HERE = Path(__file__).parent
SOUL  = (HERE / "soul" / "FRIDAY.md").read_text()
SKILL = "\n\n---\n\n".join(p.read_text() for p in sorted((HERE / "skills").glob("*.md")))


async def _run(update: Update, inputs):
    async def keep_typing():
        while True:
            await update.message.reply_chat_action("typing")
            await asyncio.sleep(4)

    typing = asyncio.create_task(keep_typing())
    try:
        turn = await thread.turn(inputs)
        text = ""
        async for event in turn.stream():
            if event.method == "item/agentMessage/delta":
                text += event.payload.delta or ""
    finally:
        typing.cancel()
    await update.message.reply_text(text.strip() or "(sin respuesta)")


async def handle_message(update: Update, _):
    await _run(update, update.message.text)


async def handle_photo(update: Update, _):
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    photo_path = HERE / "data" / "photos" / "recipes" / f"{uuid.uuid4().hex}.jpg"
    photo_path.parent.mkdir(parents=True, exist_ok=True)
    await (await photo.get_file()).download_to_drive(str(photo_path))
    inputs = [LocalImageInput(path=str(photo_path))]
    if caption:
        inputs.append(caption)
    await _run(update, inputs)


async def post_init(app):
    global thread
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "friday.db").touch()
    codex = await AsyncCodex().__aenter__()
    thread = await codex.thread_start(model=MODEL, cwd=str(HERE), developer_instructions=SOUL, base_instructions=SKILL)


app = (
    ApplicationBuilder()
    .token(TELEGRAM_TOKEN)
    .post_init(post_init)
    .build()
)
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
