import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from groq import Groq
from aiohttp import web

# --- Environment Setup ---
load_dotenv()
DISCORD_TOKEN = os.environ.get("NA_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Initialize Groq Client
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- Low-RAM Discord Bot Configuration ---
# Disable heavy caching (members/presences) to stay under 512MB RAM limit
intents = discord.Intents.default()
intents.message_content = True
intents.members = False
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Groq AI Query Handler ---
def get_nikilis_response(user_prompt: str) -> str:
    if not groq_client:
        return "GROQ_API_KEY is not configured properly!"
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Nikilis, the creator and lead developer of Murder Mystery 2 (MM2) on Roblox. "
                        "Talk about game updates, trading, godlies (like Nik's Scythe), and dev secrets. "
                        "Keep your responses concise, friendly, and under 30 words."
                    )
                },
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=100
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error querying Groq: {e}")
        return "Sorry, I'm currently working on the next MM2 patch!"

# --- Discord Events ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Nikilis AI Discord Bot is online.")

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Respond if mentioned or if addressed directly in a DM
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Strip out the bot mention tag
        clean_content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not clean_content:
            clean_content = "Hello!"

        async with message.channel.typing():
            # Offload blocking API calls to prevent lagging the async event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, get_nikilis_response, clean_content)
            await message.reply(response)

    await bot.process_commands(message)

# --- Lightweight Web Server for Render Health Checks ---
async def handle_ping(request):
    return web.Response(text="DescAI Nikilis Bot is running alive and well!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/health', handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render assigns dynamic port numbers via $PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Health check web server running on port {port}")

# --- Combined Execution Engine ---
async def main():
    if not DISCORD_TOKEN:
        print("CRITICAL ERROR: NA_TOKEN is missing from environment variables.")
        return

    # Run the web server and the Discord bot concurrently in one loop
    await start_web_server()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutting down...")
