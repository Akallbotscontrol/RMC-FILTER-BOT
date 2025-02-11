from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
from info import API_ID, API_HASH, ADMIN, LOG_CHANNEL  # Ensure these are defined in `info.py`
from utils import get_group, update_group
from plugins.generate import database

# Bot Client (Replace "YOUR_BOT_TOKEN" with actual token)
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token="YOUR_BOT_TOKEN")

async def get_user_session():
    """Retrieve the user session from the database."""
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return None
    return Client("post_search", session_string=vj["session"], api_id=API_ID, api_hash=API_HASH)

async def get_group_details(chat_id):
    """Fetch group details from the database."""
    try:
        return await get_group(chat_id)
    except Exception:
        return None

@bot.on_message(filters.group & filters.command("connect"))
async def connect(bot, message):
    """Handles the /connect command to link a group to a channel."""
    m = await message.reply("Connecting...")

    user_session = await get_user_session()
    if user_session is None:
        return await message.reply("**Contact Admin to log in to the bot.**")

    await user_session.connect()
    user = await user_session.get_me()

    group = await get_group_details(message.chat.id)
    if group is None:
        return await bot.leave_chat(message.chat.id)

    user_id = group["user_id"]
    user_name = group["user_name"]
    verified = group["verified"]
    channels = group["channels"].copy()

    if message.from_user.id != user_id:
        return await m.edit(f"<b>Only {user_name} can use this command.</b> 😁")
    
    if not verified:
        return await m.edit("💢 <b>This chat is not verified!\n⭕ Use /verify</b>")

    try:
        channel = int(message.command[-1])
        if channel in channels:
            return await m.edit("💢 <b>This channel is already connected! You can't connect again.</b>")
        channels.append(channel)
    except ValueError:
        return await m.edit("❌ <b>Incorrect format! Use:</b> `/connect ChannelID`")
    
    try:
        chat = await bot.get_chat(channel)
        c_link = chat.invite_link
        await user_session.join_chat(c_link)
    except UserAlreadyParticipant:
        pass
    except Exception as e:
        return await m.edit(f"❌ <b>Error:</b> `{str(e)}`\n⭕ <b>Ensure I'm admin in both the channel and group.</b>")
    
    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"💢 <b>Successfully connected to [{chat.title}]({c_link})!</b>", disable_web_page_preview=True)

    log_text = f"#NewConnection\n\nUser: {message.from_user.mention}\nGroup: {message.chat.title}\nChannel: [{chat.title}]({c_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=log_text)

@bot.on_message(filters.group & filters.command("disconnect"))
async def disconnect(bot, message):
    """Handles the /disconnect command to unlink a group from a channel."""
    user_session = await get_user_session()
    if user_session is None:
        return await message.reply("**Contact Admin to log in to the bot.**")

    await user_session.connect()
    m = await message.reply("Please wait...")  

    group = await get_group_details(message.chat.id)
    if group is None:
        return await bot.leave_chat(message.chat.id)

    user_id = group["user_id"]
    user_name = group["user_name"]
    verified = group["verified"]
    channels = group["channels"].copy()

    if message.from_user.id != user_id:
        return await m.edit(f"Only {user_name} can use this command. 😁")
    
    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")    

    try:
        channel = int(message.command[-1])
        if channel not in channels:
            return await m.edit("<b>This channel is not connected yet. Check the Channel ID.</b>")
        channels.remove(channel)
    except ValueError:
        return await m.edit("❌ <b>Incorrect format! Use:</b> `/disconnect ChannelID`")
    
    try:
        chat = await bot.get_chat(channel)
        await user_session.leave_chat(channel)
    except Exception as e:
        return await m.edit(f"❌ <b>Error:</b> `{str(e)}`\n💢 <b>Ensure I'm admin in both the channel and group.</b>")

    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"💢 <b>Successfully disconnected from [{chat.title}]({chat.invite_link})!</b>", disable_web_page_preview=True)

    log_text = f"#DisConnection\n\nUser: {message.from_user.mention}\nGroup: {message.chat.title}\nChannel: [{chat.title}]({chat.invite_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=log_text)

@bot.on_message(filters.group & filters.command("connections"))
async def connections(bot, message):
    """Handles the /connections command to show linked channels."""
    group = await get_group_details(message.chat.id)
    if group is None:
        return await bot.leave_chat(message.chat.id)

    user_id = group["user_id"]
    user_name = group["user_name"]
    channels = group["channels"]
    f_sub = group.get("f_sub", None)

    if message.from_user.id != user_id:
        return await message.reply(f"<b>Only {user_name} can use this command.</b> 😁")

    if not channels:
        return await message.reply("<b>This group is not connected to any channels. Use /connect to add one.</b>")

    text = "This group is currently connected to:\n\n"
    for channel in channels:
        try:
            chat = await bot.get_chat(channel)
            text += f"🔗 <b>Connected Channel - [{chat.title}]({chat.invite_link})</b>\n"
        except Exception as e:
            await message.reply(f"❌ Error in `{channel}`:\n`{e}`")
    
    if f_sub:
        try:
            f_chat = await bot.get_chat(f_sub)
            text += f"\nFSub: [{f_chat.title}]({f_chat.invite_link})"
        except Exception as e:
            await message.reply(f"❌ <b>Error in FSub</b> (`{f_sub}`)\n`{e}`")
    
    await message.reply(text=text, disable_web_page_preview=True)

# Run the bot
bot.run()
