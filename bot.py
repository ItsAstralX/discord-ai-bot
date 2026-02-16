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

    # -------- DOCUMENTATION ----------
    if message.content.startswith("t!documentation"):
        doc = """
**🧠 TerminusAI Commands**

`t!watch #channel`  
→ Choose which channel to summarize  

`t!sendhere #channel`  
→ Choose where summaries get sent  

`t!start`  
→ Start summarizing  

`t!stop`  
→ Stop summarizing  

**How it works:**  
Bot watches chosen channel and summarizes every 20 messages  
into 1-2 short sentences.
"""
        await message.channel.send(doc)
        return

    # -------- SET WATCH CHANNEL ----------
    if message.content.startswith("t!watch"):
        if message.channel_mentions:
            watch_channel_id = message.channel_mentions[0].id
            await message.channel.send(f"👀 Watching {message.channel_mentions[0].mention}")
        else:
            await message.channel.send("Usage: t!watch #channel")
        return

    # -------- SET SEND CHANNEL ----------
    if message.content.startswith("t!sendhere"):
        if message.channel_mentions:
            send_channel_id = message.channel_mentions[0].id
            await message.channel.send(f"🧠 Summaries will go to {message.channel_mentions[0].mention}")
        else:
            await message.channel.send("Usage: t!sendhere #channel")
        return

    # -------- START ----------
    if message.content == "t!start":
        active = True
        buffer = []
        await message.channel.send("✅ Summarizer ON")
        return

    # -------- STOP ----------
    if message.content == "t!stop":
        active = False
        await message.channel.send("🛑 Summarizer OFF")
        return

    # -------- MESSAGE TRACKING ----------
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
Keep it concise and clear.

{text}
"""

    res = ai.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )

    summary = res.choices[0].message.content.strip()

    await send_channel.send(f"🧠 {summary}")

bot.run(DISCORD_TOKEN)
