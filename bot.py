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

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"🔥 Bot online as {bot.user}")

# ---------- EMBED HELPER ----------
def make_embed(text, color=0x8a2be2):
    return discord.Embed(description=text, color=color)

# ---------- MESSAGE EVENT ----------
@bot.event
async def on_message(message):
    global watch_channel_id, send_channel_id, active, buffer

    if message.author.bot:
        return

    content = message.content.lower()

    # ---------- DOCUMENTATION ----------
    if content.startswith("t!documentation"):
        e = discord.Embed(title="📘 TerminusAI Commands", color=0x8a2be2)
        e.add_field(name="t!watch #channel", value="Set channel to summarize", inline=False)
        e.add_field(name="t!sendhere #channel", value="Where summaries go", inline=False)
        e.add_field(name="t!start", value="Start summarizing", inline=False)
        e.add_field(name="t!stop", value="Stop summarizing", inline=False)
        e.set_footer(text="Summarizes every 20 messages in 1–2 sentences.")
        await message.channel.send(embed=e)
        return

    # ---------- WATCH CHANNEL ----------
    if content.startswith("t!watch"):
        if message.channel_mentions:
            watch_channel_id = message.channel_mentions[0].id
            await message.channel.send(embed=make_embed(f"👀 Watching {message.channel_mentions[0].mention}"))
        else:
            await message.channel.send(embed=make_embed("Usage: t!watch #channel", 0xff0000))
        return

    # ---------- SEND CHANNEL ----------
    if content.startswith("t!sendhere"):
        if message.channel_mentions:
            send_channel_id = message.channel_mentions[0].id
            await message.channel.send(embed=make_embed(f"🧠 Summaries will go to {message.channel_mentions[0].mention}"))
        else:
            await message.channel.send(embed=make_embed("Usage: t!sendhere #channel", 0xff0000))
        return

    # ---------- START ----------
    if content == "t!start":
        active = True
        buffer = []
        await message.channel.send(embed=make_embed("✅ Summarizer started"))
        print("✅ Summarizer activated")
        return

    # ---------- STOP ----------
    if content == "t!stop":
        active = False
        await message.channel.send(embed=make_embed("🛑 Summarizer stopped"))
        print("🛑 Summarizer stopped")
        return

    # ---------- TRACK MESSAGES ----------
    if not active:
        return

    if watch_channel_id is None or send_channel_id is None:
        return

    if message.channel.id != watch_channel_id:
        return

    buffer.append(f"{message.author.display_name}: {message.content}")
    print(f"📥 Message added. Buffer size: {len(buffer)}")

    if len(buffer) >= 20:
        await summarize_and_send(message.guild)
        buffer = []

# ---------- SUMMARY ----------
async def summarize_and_send(guild):
    global buffer

    print("⚠️ Summarizing now...")

    send_channel = guild.get_channel(send_channel_id)
    if not send_channel:
        print("❌ Send channel not found")
        return

    if not buffer:
        print("❌ Buffer empty")
        return

    text = "\n".join(buffer)

    try:
        prompt = f"Summarize this Discord conversation in ONLY 1-2 short sentences:\n{text}"

        res = ai.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}]
        )

        summary = res.choices[0].message.content.strip()
        print("✅ Summary created:", summary)

        await send_channel.send(embed=make_embed(f"🧠 {summary}"))

    except Exception as e:
        print("❌ OPENAI ERROR:", e)
        await send_channel.send("Error generating summary.")

bot.run(DISCORD_TOKEN)
