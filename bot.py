import discord
import os
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

ai = OpenAI(api_key=OPENAI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

watch_channel_id = None
send_channel_id = None
active = False
buffer = []

# -------- READY ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# -------- COMMANDS ----------
@bot.event
async def on_message(message):
    global watch_channel_id, send_channel_id, active, buffer

    if message.author.bot:
        return

    # ---- COMMAND: set watch channel
    if message.content.startswith("!watch"):
        if message.channel_mentions:
            watch_channel_id = message.channel_mentions[0].id
            await message.channel.send(f"👀 Now watching {message.channel_mentions[0].mention}")
        return

    # ---- COMMAND: set send channel
    if message.content.startswith("!sendhere"):
        if message.channel_mentions:
            send_channel_id = message.channel_mentions[0].id
            await message.channel.send(f"🧠 Summaries will go to {message.channel_mentions[0].mention}")
        return

    # ---- START
    if message.content == "!start":
        active = True
        buffer = []
        await message.channel.send("✅ Summarizer ON")
        return

    # ---- STOP
    if message.content == "!stop":
        active = False
        await message.channel.send("🛑 Summarizer OFF")
        return

    # ---- MESSAGE TRACKING
    if not active:
        return

    if watch_channel_id is None or send_channel_id is None:
        return

    if message.channel.id != watch_channel_id:
        return

    buffer.append(f"{message.author.display_name}: {message.content}")

    if len(buffer) >= 20:
        await summarize_and_send(message.guild)
        buffer = []

# -------- SUMMARY ----------
async def summarize_and_send(guild):
    global buffer

    send_channel = guild.get_channel(send_channel_id)
    if not send_channel:
        return

    text = "\n".join(buffer)

    prompt = f"""
Summarize this Discord conversation in ONLY 1-2 short sentences.
Be concise and clear.

{text}
"""

    res = ai.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )

    summary = res.choices[0].message.content.strip()

    await send_channel.send(f"🧠 {summary}")

bot.run(DISCORD_TOKEN)
