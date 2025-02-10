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

# Cache admin session to improve performance
ADMIN_SESSION = None

async def send_message_in_chunks(client, chat_id, text, reply_to_id=None):
    """Send messages in chunks with reply tracking"""
    max_length = 4096
    messages = []
    for i in range(0, len(text), max_length):
        msg = await client.send_message(
            chat_id=chat_id,
            text=text[i:i+max_length],
            reply_to_message_id=reply_to_id,
            disable_web_page_preview=True
        )
        messages.append(msg)
        asyncio.create_task(delete_after_delay(msg, 1800))
    return messages

async def delete_after_delay(message: Message, delay):
    """Auto-delete messages after delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

async def perform_search(session, query, channels):
    """Optimized search function with parallel processing"""
    results = []
    seen = set()
    
    async with Client("searcher", 
                    session_string=session,
                    api_hash=API_HASH,
                    api_id=API_ID) as user_client:
        
        # Search all channels in parallel
        tasks = []
        for channel in channels:
            tasks.append(user_client.search_messages(channel, query))
        
        for channel_task in asyncio.as_completed(tasks):
            try:
                async for msg in await channel_task:
                    if content := msg.text or msg.caption:
                        name = content.split("\n", 1)[0]
                        if name not in seen:
                            seen.add(name)
                            results.append(f"🎬 {name}\n🔗 {msg.link}")
                            if len(results) >= 15:  # Limit results for speed
                                return results
            except Exception:
                continue
    return results

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def handle_search(bot, message):
    """Main search handler with user-friendly features"""
    global ADMIN_SESSION
    
    try:
        # Get original message context
        original_msg_id = message.id
        user_mention = message.from_user.mention()
        query = message.text.strip()
        
        # Validate session
        if not ADMIN_SESSION:
            admin_data = database.find_one({"chat_id": ADMIN})
            if not admin_data:
                return await message.reply("🔧 Bot maintenance in progress...")
            ADMIN_SESSION = admin_data['session']
        
        # Force subscription check
        if not await force_sub(bot, message):
            return
        
        # Get channels
        group_data = await get_group(message.chat.id)
        channels = group_data.get("channels", [])
        if not channels:
            return
        
        # Show searching status
        search_msg = await message.reply(f"🔍 Searching for '{query}'...", 
                                       reply_to_message_id=original_msg_id)
        
        # Perform optimized search
        results = await perform_search(ADMIN_SESSION, query, channels)
        
        # Process results
        if results:
            header = f"🎯 **Results for '{query}'** ({len(results)} found)\n\n"
            response = header + "\n\n".join(results[:10])  # Show top 10 results
            footer = f"\n\n💡 Powered by @VJ_Botz | 👤 {user_mention}"
            await send_message_in_chunks(bot, message.chat.id, response+footer, original_msg_id)
        else:
            # Show IMDB suggestions
            movies = await search_imdb(query)
            buttons = [
                [InlineKeyboardButton(
                    f"🎞 {movie['title']} ({movie.get('year', 'N/A')})",
                    callback_data=f"recheck_{movie['id']}"
                )] for movie in movies[:5]  # Top 5 suggestions
            ]
            await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption=f"❌ No results found for: {query}\nTry these suggestions:",
                reply_to_message_id=original_msg_id,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        await search_msg.delete()
        
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}", reply_to_message_id=original_msg_id)

@Client.on_callback_query(filters.regex(r"^recheck"))
async def handle_recheck(bot, update):
    """Improved recheck handler with context"""
    try:
        user_id = update.from_user.id
        original_msg = update.message.reply_to_message
        
        # Validate user context
        if not original_msg or user_id != original_msg.from_user.id:
            return await update.answer("⚠️ This isn't your search!", show_alert=True)
        
        # Show processing status
        await update.message.edit("⏳ Verifying title...")
        
        # Get search parameters
        imdb_id = update.data.split("_")[1]
        query = await search_imdb(imdb_id)
        channels = (await get_group(update.message.chat.id)).get("channels", [])
        
        # Perform search
        results = await perform_search(ADMIN_SESSION, query, channels)
        
        if results:
            header = f"✅ **Found results for '{query}'**\n\n"
            response = header + "\n\n".join(results[:10])
            footer = f"\n\n🔍 Corrected search | @VJ_Botz"
            await send_message_in_chunks(bot, update.message.chat.id, response+footer, original_msg.id)
            await update.message.delete()
        else:
            await update.message.edit(
                f"❌ Still no results for: {query}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📩 Request to Admin", callback_data=f"request_{imdb_id}")
                ]])
            )
            
    except Exception as e:
        await update.message.edit(f"⚠️ Error: {str(e)}")

@Client.on_callback_query(filters.regex(r"^request"))
async def handle_request(bot, update):
    """Enhanced request handler with context"""
    try:
        user_id = update.from_user.id
        original_msg = update.message.reply_to_message
        
        # Validate user context
        if not original_msg or user_id != original_msg.from_user.id:
            return await update.answer("⚠️ This isn't your request!", show_alert=True)
        
        # Get request details
        imdb_id = update.data.split("_")[1]
        movie_title = await search_imdb(imdb_id)
        admin_id = (await get_group(update.message.chat.id)).get("user_id")
        
        # Prepare request message
        request_text = (
            f"📬 **New Content Request**\n\n"
            f"👤 From: {update.from_user.mention}\n"
            f"📝 Original Query: `{original_msg.text}`\n"
            f"🎬 Title: {movie_title}\n"
            f"🔗 IMDb: https://www.imdb.com/title/tt{imdb_id}"
        )
        
        # Send to admin with context
        await bot.send_message(
            admin_id,
            request_text,
            disable_web_page_preview=True,
            reply_to_message_id=original_msg.id
        )
        
        await update.answer("✅ Request sent to admin!", show_alert=True)
        await update.message.delete()
        
    except Exception as e:
        await update.message.edit(f"⚠️ Request failed: {str(e)}")
