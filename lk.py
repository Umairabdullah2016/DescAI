import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq
from aiohttp import web

# --------------------------------------------------
# 1. Environment & Setup
# --------------------------------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Nosniy Token
SG_TOKEN = os.getenv("SG_TOKEN")            # SenseiWarrior Token
NA_TOKEN = os.getenv("NA_TOKEN")            # Neko Token
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 8080))         # Default port for Render health checks

if not DISCORD_TOKEN or not SG_TOKEN or not NA_TOKEN or not GROQ_API_KEY:
    exit(1)

# Initialize Groq Client
groq_client = Groq(api_key=GROQ_API_KEY)

def ask_groq_ai(prompt: str, bot_identity: str) -> str:
    """Fetch fast AI responses using Groq."""
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"You are {bot_identity}, a helpful and friendly Discord AI assistant."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="openai/gpt-oss-120b",
    )
    return chat_completion.choices[0].message.content

# --------------------------------------------------
# 2. Render Dummy Health Check Web Server
# --------------------------------------------------
async def handle_health_check(request):
    """Satisfies Render's mandatory HTTP health check."""
    return web.Response(text="All 3 bots are online and healthy!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

# --------------------------------------------------
# 3. Bot Factory Function
# --------------------------------------------------
def create_bot(bot_identity: str):
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents, max_messages=None)

    @bot.command(name="ask")
    async def ask_ai(ctx, *, prompt: str):
        async with ctx.typing():
            try:
                response = await asyncio.to_thread(ask_groq_ai, prompt, bot_identity)
                if len(response) > 2000:
                    response = response[:1995] + "..."
                await ctx.reply(response)
            except Exception as e:
                await ctx.reply(f"AI Error: {e}")

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        if bot.user.mentioned_in(message) and not message.mention_everyone:
            clean_content = message.content.replace(f'<@{bot.user.id}>', '').strip()
            async with message.channel.typing():
                try:
                    response = await asyncio.to_thread(ask_groq_ai, clean_content, bot_identity)
                    if len(response) > 2000:
                        response = response[:1995] + "..."
                    await message.reply(response)
                except Exception as e:
                    await message.reply(f"Error: {e}")

        await bot.process_commands(message)

    return bot

# Initialize Bot Instances
nosniy_bot = create_bot("Nosniy")
sensei_bot = create_bot("SenseiWarrior")
neko_bot = create_bot("Neko")

# --------------------------------------------------
# 4. Concurrent Execution
# --------------------------------------------------
async def main():
    # Start internal web server alongside bots
    await start_web_server()
    
    async with nosniy_bot, sensei_bot, neko_bot:
        await asyncio.gather(
            nosniy_bot.start(DISCORD_TOKEN),
            sensei_bot.start(SG_TOKEN),
            neko_bot.start(NA_TOKEN)
        )

if __name__ == "__main__":
    asyncio.run(main())
