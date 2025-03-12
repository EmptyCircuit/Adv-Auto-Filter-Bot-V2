from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

bot = Client(
    "AutoFilterBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# Connect to MongoDB
mongo_client = AsyncIOMotorClient(Config.MONGO_URI)
db = mongo_client[Config.DB_NAME]
collection = db[Config.COLLECTION_NAME]

# Store files in MongoDB
@bot.on_message(filters.document | filters.video | filters.audio)
async def save_file(client, message):
    file_data = {
        "file_id": message.document.file_id if message.document else message.video.file_id if message.video else message.audio.file_id,
        "file_name": message.document.file_name if message.document else message.video.file_name if message.video else message.audio.file_name,
        "chat_id": message.chat.id,
        "message_id": message.message_id
    }
    await collection.insert_one(file_data)
    await message.reply_text("✅ File saved successfully!")

# Search files when a user sends a text message
@bot.on_message(filters.text)
async def search_file(client, message):
    query = message.text
    results = collection.find({"file_name": {"$regex": query, "$options": "i"}})
    
    files = []
    async for file in results:
        files.append(
            f"📂 {file['file_name']}\n"
            f"/get_{file['file_id']}"
        )
    
    if files:
        await message.reply_text("\n\n".join(files))
    else:
        await message.reply_text("❌ No files found!")

# Send file when requested
@bot.on_message(filters.command("get_"))
async def send_file(client, message):
    file_id = message.command[0].split("_")[1]
    file_data = await collection.find_one({"file_id": file_id})
    
    if file_data:
        await message.reply_document(file_data["file_id"])
    else:
        await message.reply_text("❌ File not found!")

bot.run()
