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
DISCORD_TOKEN = os.environ.get("NA_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Set a 15-second timeout on the Groq client to prevent infinite hangs
groq_client = (
    Groq(api_key=GROQ_API_KEY, timeout=15.0) if GROQ_API_KEY else None
)

# Dedicated thread pool for low-RAM background API calls
executor = ThreadPoolExecutor(max_workers=2)

# --- Low-RAM Discord Bot Configuration ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = False
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)


# --- Groq AI Query Handler ---
def get_nikilis_response(user_prompt: str) -> str:
  if not groq_client:
    return (
        "⚠️ **Error:** `GROQ_API_KEY` is missing from Render environment"
        " variables!"
    )

  try:
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Using Groq's active stable endpoint
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Nikilis, the creator and lead developer of Murder"
                    " Mystery 2 (MM2) on Roblox. Talk about game updates,"
                    " trading, godlies (like Nik's Scythe), and dev secrets."
                    " Keep your responses concise, friendly, and under 30 words."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=250,  # Increased to prevent mid-sentence cutoffs
        temperature=0.7,
    )
    content = completion.choices[0].message.content
    return content if content else "⚠️ **Error:** Received empty response from API."
  except Exception as e:
    error_msg = str(e) if str(e) else repr(e)
    return f"⚠️ **Groq API Error:** `{error_msg}`"


# --- Discord Events ---
@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  print("Nikilis AI Discord Bot is online.")


@bot.event
async def on_message(message):
  if message.author == bot.user:
    return

  if bot.user.mentioned_in(message) or isinstance(
      message.channel, discord.DMChannel
  ):
    clean_content = message.content.replace(f'<@{bot.user.id}>', '').strip()

    if not clean_content:
      clean_content = "Hello!"

    async with message.channel.typing():
      try:
        # Enforce a 20-second hard limit on the async execution
        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                executor, get_nikilis_response, clean_content
            ),
            timeout=20.0,
        )
        await message.reply(response)
      except asyncio.TimeoutError:
        await message.reply(
            "⚠️ **Timeout Error:** The API request took too long to respond."
        )
      except Exception as e:
        await message.reply(f"⚠️ **Execution Error:** `{e}`")

  await bot.process_commands(message)


# --- Lightweight Web Server for Render Health Checks ---
async def handle_ping(request):
  return web.Response(
      text="DescAI Nikilis Bot is running alive and well!", status=200
  )


async def start_web_server():
  app = web.Application()
  app.router.add_get('/', handle_ping)
  app.router.add_get('/health', handle_ping)

  runner = web.AppRunner(app)
  await runner.setup()

  port = int(os.environ.get("PORT", 8080))
  site = web.TCPSite(runner, '0.0.0.0', port)
  await site.start()
  print(f"Health check web server running on port {port}")


# --- Combined Execution Engine ---
async def main():
  if not DISCORD_TOKEN:
    print("CRITICAL ERROR: NA_TOKEN is missing from environment variables.")
    return

  await start_web_server()
  await bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("Bot shutting down...")
