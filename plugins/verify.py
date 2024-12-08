from info import *  # Ensure this file contains required functions like get_group, update_group, etc.
from utils import *  # Ensure utils file contains relevant helper functions
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton 

@Client.on_message(filters.group & filters.command("verify"))
async def _verify(bot, message):
    try:
        # Fetch group data from your database or source
        group = await get_group(message.chat.id)
        user_id = group["user_id"]
        user_name = group["user_name"]
        verified = group["verified"]
    except Exception as e:
        # If group info cannot be fetched, the bot leaves the chat
        print(f"Error fetching group data: {e}")
        return await bot.leave_chat(message.chat.id)  

    try:
        user = await bot.get_users(user_id)
    except Exception as e:
        # Handle user fetching failure
        print(f"Error fetching user {user_id}: {e}")
        return await message.reply(f"❌ {user_name} needs to start me in PM!")

    if message.from_user.id != user_id:
        return await message.reply(f"<b>Only {user.mention} can use this command 😁</b>")

    if verified:
        return await message.reply("<b>This Group is already verified!</b>")

    try:
        # Fetch the group invite link
        link = (await bot.get_chat(message.chat.id)).invite_link     
    except Exception as e:
        # Handle error if invite link can't be fetched
        print(f"Error fetching group invite link: {e}")
        return message.reply("❌ <b>Make me admin here with all permissions!</b>")    

    # Build the request message
    text = f"#NewRequest\n\n"
    text += f"User: {message.from_user.mention}\n"
    text += f"User ID: `{message.from_user.id}`\n"
    text += f"Group: [{message.chat.title}]({link})\n"
    text += f"Group ID: `{message.chat.id}`\n"
   
    # Send request to the log channel for approval
    await bot.send_message(
        chat_id=LOG_CHANNEL,
        text=text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Approve", callback_data=f"verify_approve_{message.chat.id}"),
              InlineKeyboardButton("❌ Decline", callback_data=f"verify_decline_{message.chat.id}")]]
        )
    )

    # Reply to the user
    await message.reply("💢 <b>Verification Request sent ✅\n🔻 We will notify You Personally when it is approved</b> ⭕")

@Client.on_callback_query(filters.regex(r"^verify"))
async def verify_(bot, update):
    # Extract group ID from callback data
    id = int(update.data.split("_")[-1])
    
    # Fetch group details
    group = await get_group(id)
    name = group["name"]
    user = group["user_id"]

    if update.data.split("_")[1] == "approve":
        # Approve the group
        await update_group(id, {"verified": True})
        await bot.send_message(chat_id=user, text=f"💢 <b>Your verification request for {name} has been approved</b> ✅")
        await update.message.edit(update.message.text.html.replace("#NewRequest", "#Approved"))
    else:
        # Decline the request
        await delete_group(id)
        await bot.send_message(chat_id=user, text=f"<b>Your verification request for {name} has been declined 😐 Please Contact Admin</b>")
        await update.message.edit(update.message.text.html.replace("#NewRequest", "#Declined"))
