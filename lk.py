import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import traceback
from aiohttp import web
from dotenv import load_dotenv
import discord
from discord.ext import commands
from groq import Groq

# --- Environment Setup ---
load_dotenv()

# Discord Tokens
NA_TOKEN = os.environ.get("NA_TOKEN")      # Bot 1: Nikilis
SGT_TOKEN = os.environ.get("SGT")         # Bot 2: SenseiWarrior
NGT_TOKEN = os.environ.get("NGT")         # Bot 3: Nosniy

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Shared Groq Client
groq_client = (
    Groq(api_key=GROQ_API_KEY, timeout=15.0) if GROQ_API_KEY else None
)

# Shared thread pool to keep memory ultra-low on Render (512MB RAM)
executor = ThreadPoolExecutor(max_workers=3)

def get_low_ram_intents():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = False
    intents.presences = False
    return intents


# --- Generic AI Generator Function ---
def get_ai_response(user_prompt: str, system_prompt: str) -> str:
    if not groq_client:
        return "⚠️ **Error:** `GROQ_API_KEY` is missing from environment variables!"

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        content = completion.choices[0].message.content
        return content if content else "⚠️ **Error:** Empty response from API."
    except Exception as e:
        return f"⚠️ **Groq API Error:** `{e}`"


# ==============================================================================
# BOT 1: NIKILIS (MM2 Creator) - NA_TOKEN
# ==============================================================================
bot_nikilis = commands.Bot(command_prefix="!", intents=get_low_ram_intents())

NIKILIS_PROMPT = (
    "You are Nikilis, creator and lead developer of Murder Mystery 2 (MM2) on Roblox. "
    "Talk about game updates, trading, godlies (like Nik's Scythe), and dev secrets. "
    "Keep responses concise, friendly, and under 30 words."
)

@bot_nikilis.event
async def on_ready():
    print(f"[Bot 1] Nikilis active as {bot_nikilis.user.name}")

@bot_nikilis.event
async def on_message(message):
    if message.author == bot_nikilis.user:
        return

    if bot_nikilis.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        clean_content = message.content.replace(f'<@{bot_nikilis.user.id}>', '').strip() or "Hello!"
        async with message.channel.typing():
            try:
                loop = asyncio.get_running_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(executor, get_ai_response, clean_content, NIKILIS_PROMPT),
                    timeout=20.0
                )
                await message.reply(response)
            except Exception as e:
                await message.reply(f"⚠️ **Error:** `{e}`")

    await bot_nikilis.process_commands(message)


# ==============================================================================
# BOT 2: SENSEIWARRIOR (Lead Programmer) - SGT
# ==============================================================================
bot_sensei = commands.Bot(command_prefix="?", intents=get_low_ram_intents())

SENSEI_PROMPT = (
    "You are SenseiWarrior, expert Roblox lead programmer and co-founder of Nosniy Games. "
    "Talk about coding game mechanics, scripting in Luau, optimizing servers, and working on games like RIVALS or Treasure Quest. "
    "Keep responses concise, technical yet friendly, and under 30 words."
)

@bot_sensei.event
async def on_ready():
    print(f"[Bot 2] SenseiWarrior active as {bot_sensei.user.name}")

@bot_sensei.event
async def on_message(message):
    if message.author == bot_sensei.user:
        return

    if bot_sensei.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        clean_content = message.content.replace(f'<@{bot_sensei.user.id}>', '').strip() or "Hello!"
        async with message.channel.typing():
            try:
                loop = asyncio.get_running_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(executor, get_ai_response, clean_content, SENSEI_PROMPT),
                    timeout=20.0
                )
                await message.reply(response)
            except Exception as e:
                await message.reply(f"⚠️ **Error:** `{e}`")

    await bot_sensei.process_commands(message)


# ==============================================================================
# BOT 3: NOSNIY (Game Studio Founder) - NGT
# ==============================================================================
bot_nosniy = commands.Bot(command_prefix=".", intents=get_low_ram_intents())

NOSNIY_PROMPT = (
    "You are Nosniy, Roblox game developer and founder of Nosniy Games. "
    "Talk about studio management, building hit Roblox games (Treasure Quest, Super Golf, RIVALS), and community events. "
    "Keep responses enthusiastic, friendly, and under 30 words."
)

@bot_nosniy.event
async def on_ready():
    print(f"[Bot 3] Nosniy active as {bot_nosniy.user.name}")

@bot_nosniy.event
async def on_message(message):
    if message.author == bot_nosniy.user:
        return

    if bot_nosniy.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        clean_content = message.content.replace(f'<@{bot_nosniy.user.id}>', '').strip() or "Hello!"
        async with message.channel.typing():
            try:
                loop = asyncio.get_running_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(executor, get_ai_response, clean_content, NOSNIY_PROMPT),
                    timeout=20.0
                )
                await message.reply(response)
            except Exception as e:
                await message.reply(f"⚠️ **Error:** `{e}`")

    await bot_nosniy.process_commands(message)


# ==============================================================================
# LIGHTWEIGHT WEB SERVER FOR RENDER
# ==============================================================================
async def handle_ping(request):
    return web.Response(text="Nikilis, SenseiWarrior, and Nosniy bots are all running smoothly!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/health', handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Render health check web server running on port {port}")


# ==============================================================================
# COMBINED EXECUTION ENGINE
# ==============================================================================
async def main():
    await start_web_server()

    tasks = []

    if NA_TOKEN:
        tasks.append(bot_nikilis.start(NA_TOKEN))
    else:
        print("CRITICAL: NA_TOKEN is missing!")

    if SGT_TOKEN:
        tasks.append(bot_sensei.start(SGT_TOKEN))
    else:
        print("CRITICAL: SGT environment variable is missing!")

    if NGT_TOKEN:
        tasks.append(bot_nosniy.start(NGT_TOKEN))
    else:
        print("CRITICAL: NGT environment variable is missing!")

    if not tasks:
        print("No valid tokens found. Exiting.")
        return

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down all 3 developer bots...")
