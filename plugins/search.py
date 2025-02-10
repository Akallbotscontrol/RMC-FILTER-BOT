# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import asyncio
from info import *
from utils import *
from time import time 
from plugins.generate import database
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

async def send_message_in_chunks(client, chat_id, text, reply_to_message_id=None):
    """Send long messages in chunks with reply support"""
    max_length = 4096
    for i in range(0, len(text), max_length):
        msg = await client.send_message(
            chat_id=chat_id,
            text=text[i:i+max_length],
            reply_to_message_id=reply_to_message_id
        )
        asyncio.create_task(delete_after_delay(msg, 1800))

async def delete_after_delay(message: Message, delay):
    """Auto-delete messages after specified delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def handle_search(bot, message):
    """Main handler for search requests"""
    # Check admin session
    admin_data = database.find_one({"chat_id": ADMIN})
    if not admin_data:
        return await message.reply("⚠️ Bot configuration error - contact admin!")

    # Force subscription check
    if not await force_sub(bot, message):
        return

    # Get configured channels
    group_data = await get_group(message.chat.id)
    if not group_data.get("channels"):
        return

    # Process query
    query = message.text.strip()
    if query.startswith("/"):
        return

    # Search in channels
    results = []
    try:
        async with Client("searcher", 
                        session_string=admin_data['session'],
                        api_hash=API_HASH,
                        api_id=API_ID) as user_client:
            
            for channel in group_data["channels"]:
                async for msg in user_client.search_messages(chat_id=channel, query=query):
                    if content := msg.text or msg.caption:
                        name = content.split("\n", 1)[0]
                        if name not in results:
                            results.append(f"🎬 {name}\n🔗 {msg.link}")

            if results:
                response = (
                    f"🔍 Results for '{query}':\n\n" +
                    "\n\n".join(results[:10]) +  # Limit to 10 results
                    f"\n\n💡 Powered by @VJ_Botz"
                )
                await send_message_in_chunks(
                    bot,
                    message.chat.id,
                    response,
                    reply_to_message_id=message.id
                )
            else:
                # Show IMDB suggestions
                movies = await search_imdb(query)
                buttons = [
                    [InlineKeyboardButton(movie['title'], callback_data=f"suggest_{movie['id']}")]
                    for movie in movies[:5]  # Show top 5 suggestions
                ]
                await message.reply_photo(
                    photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                    caption="❌ No results found! Try these suggestions:",
                    reply_markup=InlineKeyboardMarkup(buttons)
                
    except Exception as e:
        await message.reply(f"⚠️ Search error: {str(e)}")

@Client.on_callback_query(filters.regex(r"^suggest_"))
async def handle_suggestion(bot, update):
    """Handle IMDB suggestion callbacks"""
    user_id = update.from_user.id
    try:
        original_user = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete()

    if user_id != original_user:
        return await update.answer("❌ This isn't your search!", show_alert=True)

    imdb_id = update.data.split("_", 1)[1]
    try:
        # Get movie details
        movie = await get_imdb_details(imdb_id)
        
        # Search again with correct title
        await update.message.edit("🔍 Searching with exact title...")
        await handle_search(bot, update.message.reply_to_message)
        
    except Exception as e:
        await update.message.edit(f"⚠️ Error: {str(e)}")

@Client.on_callback_query(filters.regex(r"^request_"))
async def handle_request(bot, update):
    """Handle content requests to admin"""
    user_id = update.from_user.id
    try:
        original_user = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete()

    if user_id != original_user:
        return await update.answer("❌ This isn't your request!", show_alert=True)

    imdb_id = update.data.split("_", 1)[1]
    try:
        # Get admin ID from group data
        group_data = await get_group(update.message.chat.id)
        admin_id = group_data["user_id"]
        
        # Get movie details
        movie = await get_imdb_details(imdb_id)
        
        # Send request to admin
        request_msg = (
            f"🚨 Content Request\n\n"
            f"📌 From: {update.from_user.mention}\n"
            f"🎬 Title: {movie['title']}\n"
            f"📅 Year: {movie['year']}\n"
            f"⭐ Rating: {movie['rating']}\n"
            f"🔗 IMDB: https://www.imdb.com/title/tt{imdb_id}"
        )
        await bot.send_message(admin_id, request_msg)
        await update.answer("✅ Request sent to admin!", show_alert=True)
        await update.message.delete()
        
    except Exception as e:
        await update.message.edit(f"⚠️ Request failed: {str(e)}")

# Add any additional utility functions from utils.py here if needed
# Make sure to implement force_sub, get_group, search_imdb, etc. in utils.py

if __name__ == "__main__":
    print("Bot started!")
    app.run()
