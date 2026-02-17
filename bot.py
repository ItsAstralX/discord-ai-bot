import discord
import os
import re
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

# ================= CLEAN + FILTER =================

def clean_message(msg: str):
    msg = msg.lower()
    msg = re.sub(r'http\S+', '', msg)              # remove links
    msg = re.sub(r'[^\w\s,.!?]', '', msg)          # remove emojis/symbols
    msg = re.sub(r'(.)\1{2,}', r'\1', msg)         # compress loooool -> lol
    msg = re.sub(r'\s+', ' ', msg).strip()
    return msg

def useful_message(msg: str):
    words = msg.split()

    if len(words) < 4:
        return False

    if msg.startswith(("y", "n")):  # remove yes/no spam
        return False

    spam = ["lol", "lmao", "hi", "ok", "bro", "nah", "yep"]
    if msg in spam:
        return False

    return True

def compress_buffer(messages, limit=120):
    cleaned = []

    for m in messages:
        msg = clean_message(m)
        if useful_message(msg):
            cleaned.append(msg)

    cleaned = cleaned[-limit:]  # HARD CAP = saves $
    return "\n".join(cleaned)

# ================= READY =================

@bot.event
async def on_ready():
    print(f"🔥 Bot online as {bot.user}")

def make_embed(text, color=0x8a2be2):
    return discord.Embed(description=text, color=color)

# ================= COMMANDS =================

@bot.event
async def on_message(message):
    global watch_channel_id, send_channel_id, active, buffer

    if message.author.bot:
        return

    content = message.content.lower()

    if content.startswith("t!documentation"):
        e = discord.Embed(title="📘 TerminusAI Commands", color=0x8a2be2)
        e.add_field(name="t!watch #channel", value="Set channel to summarize", inline=False)
        e.add_field(name="t!sendhere #channel", value="Where summaries go", inline=False)
        e.add_field(name="t!start", value="Start summarizing", inline=False)
        e.add_field(name="t!stop", value="Stop summarizing", inline=False)
        e.set_footer(text="Ultra-cheap optimized summarizer.")
        await message.channel.send(embed=e)
        return

    if content.startswith("t!watch"):
        if message.channel_mentions:
            watch_channel_id = message.channel_mentions[0].id
            await message.channel.send(embed=make_embed(f"👀 Watching {message.channel_mentions[0].mention}"))
        else:
            await message.channel.send(embed=make_embed("Usage: t!watch #channel", 0xff0000))
        return

    if content.startswith("t!sendhere"):
        if message.channel_mentions:
            send_channel_id = message.channel_mentions[0].id
            await message.channel.send(embed=make_embed(f"🧠 Sending summaries to {message.channel_mentions[0].mention}"))
        else:
            await message.channel.send(embed=make_embed("Usage: t!sendhere #channel", 0xff0000))
        return

    if content == "t!start":
        active = True
        buffer = []
        await message.channel.send(embed=make_embed("✅ Summarizer started"))
        return

    if content == "t!stop":
        active = False
        await message.channel.send(embed=make_embed("🛑 Summarizer stopped"))
        return

    # ================= TRACK =================

    if not active:
        return
    if watch_channel_id is None or send_channel_id is None:
        return
    if message.channel.id != watch_channel_id:
        return

    buffer.append(message.content)

    # summarize every 80 msgs (cheap but effective)
    if len(buffer) >= 80:
        await summarize_and_send(message.guild)
        buffer = []

# ================= SUMMARY =================

async def summarize_and_send(guild):
    global buffer

    send_channel = guild.get_channel(send_channel_id)
    if not send_channel or not buffer:
        return

    compressed = compress_buffer(buffer)

    if not compressed.strip():
        return

    try:
        prompt = f"""
Summarize this Discord chat into EXACTLY 6 short bullet points.
No fluff. No filler. Focus only on meaningful discussions.

Chat:
{compressed}
"""

        res = ai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120
        )

        summary = res.choices[0].message.content.strip()

        usage = res.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        cost_input = input_tokens * 0.00000015
        cost_output = output_tokens * 0.0000006
        total_cost = cost_input + cost_output

        cost_text = f"-# {total_tokens} tokens • ${total_cost:.6f}"

        await send_channel.send(
            embed=make_embed(f"🧠 **Server Summary**\n{summary}\n{cost_text}")
        )

        print(f"💰 {total_tokens} tokens | ${total_cost:.6f}")

    except Exception as e:
        print("❌ OPENAI ERROR:", e)
        await send_channel.send("Error generating summary.")

bot.run(DISCORD_TOKEN)
