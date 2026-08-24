import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

# --------------------------------------------------
# 1. Environment & Setup
# --------------------------------------------------
print("🔄 Loading environment variables...")
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DISCORD_TOKEN:
    print("❌ Error: Missing DISCORD_TOKEN in .env file!")
    exit(1)

if not GROQ_API_KEY:
    print("❌ Error: Missing GROQ_API_KEY in .env file!")
    exit(1)

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Groq Client
groq_client = Groq(api_key=GROQ_API_KEY)

# --------------------------------------------------
# 2. AI Helper Function
# --------------------------------------------------
def ask_groq_ai(prompt: str) -> str:
    """Fetch fast, keyless-tier AI responses using Groq."""
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are Nosniy, a helpful and friendly Discord AI assistant."
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
# 3. Discord Events & Commands
# --------------------------------------------------
@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"🟢 ACTIVE: {bot.user.name} is online and connected to Groq!")
    print("--------------------------------------------------")

@bot.command(name="ask")
async def ask_ai(ctx, *, prompt: str):
    print(f"\n📩 Command received: '!ask {prompt}'")
    async with ctx.typing():
        try:
            # Run blocking API call in an async thread to prevent Discord lag
            response = await asyncio.to_thread(ask_groq_ai, prompt)
            
            if len(response) > 2000:
                response = response[:1995] + "..."
                
            await ctx.reply(response)
            print("✅ Response sent!")
        except Exception as e:
            print(f"❌ Error: {e}")
            await ctx.reply(f"AI Error: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) and not message.mention_everyone:
        clean_content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        print(f"\n💬 Mention received: '{clean_content}'")
        
        async with message.channel.typing():
            try:
                response = await asyncio.to_thread(ask_groq_ai, clean_content)
                
                if len(response) > 2000:
                    response = response[:1995] + "..."
                    
                await message.reply(response)
                print("✅ Response sent!")
            except Exception as e:
                print(f"❌ Error: {e}")
                await message.reply(f"Error: {e}")

    await bot.process_commands(message)

# --------------------------------------------------
# 4. Run Bot
# --------------------------------------------------
bot.run(DISCORD_TOKEN)