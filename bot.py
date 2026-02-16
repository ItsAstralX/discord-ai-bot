import discord
import os
import asyncio
from openai import OpenAI

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

ai = OpenAI(api_key=OPENAI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

GENERAL = "general"
RECAP = "ai-recaps"

message_buffer = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    global message_buffer

    if message.author.bot:
        return
    if message.channel.name != GENERAL:
        return

    message_buffer.append(f"{message.author.display_name}: {message.content}")

    if len(message_buffer) >= 20:
        await send_summary(message.guild)
        message_buffer = []

async def send_summary(guild):
    channel = discord.utils.get(guild.text_channels, name=RECAP)
    if not channel:
        return

    text = "\n".join(message_buffer)

    res = ai.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": f"Summarize this discord chat:\n{text}"}]
    )

    summary = res.choices[0].message.content

    await channel.send(f"🧠 **20 message summary:**\n{summary}")

bot.run(DISCORD_TOKEN)
