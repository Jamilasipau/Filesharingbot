import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import json
import logging
from time import time, sleep

# Bot configuration
BOT_TOKEN = "7882079471:AAE7TnU5mGYYfZK8kaVu3YC6fvO-Xz7WDNU"
PRIVATE_CHANNEL_ID = -1002367696663  # Your private channel ID
ADMIN_ID = 6897739611  # Your admin user ID
CHANNEL_USERNAME = "@join_hyponet"  # Replace with your channel's username

bot = telebot.TeleBot(BOT_TOKEN)

# File to store button-file mappings
DATA_FILE = "menu_data.json"

# Set up logging to monitor any issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load existing button-file mappings
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save button-file mappings
def save_data(data):
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(data, file)
    except IOError as e:
        logging.error(f"Error saving data: {e}")

button_data = load_data()

# Helper function to check if the user is a member of the channel
membership_cache = {}

def is_user_member(user_id):
    current_time = time()
    
    # Clear the cached status on each check (forces a fresh status check)
    if user_id in membership_cache:
        del membership_cache[user_id]
    
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        logging.info(f"User {user_id} status: {status}")
        is_member = status in ["member", "administrator", "creator"]
        membership_cache[user_id] = (is_member, current_time)
        return is_member
    except telebot.apihelper.ApiTelegramException as e:
        if "USER_NOT_FOUND" in str(e):
            logging.warning(f"User {user_id} not found in channel.")
        else:
            logging.error(f"Error checking membership: {e}")
        return False

# Start command handler
@bot.message_handler(commands=["start"])
def start(message):
    try:
        if is_user_member(message.from_user.id):
            # Generate menu buttons
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for button_name in button_data.keys():
                markup.add(KeyboardButton(button_name))
            bot.send_message(
                message.chat.id,
                "𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐅𝐢𝐥𝐞 𝐒𝐡𝐚𝐫𝐢𝐧𝐠 𝐁𝐨𝐭 𝐁𝐲 @botplays90\n\n𝐔𝐬𝐞 𝐓𝐡𝐞 𝐁𝐞𝐥𝐨𝐰 𝐁𝐮𝐭𝐭𝐨𝐧𝐬 𝐓𝐨 𝐆𝐞𝐭 𝐅𝐢𝐥𝐞𝐬",
                reply_markup=markup,
            )
        else:
            # Prompt user to join the channel
            markup = InlineKeyboardMarkup()
            join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")
            check_button = InlineKeyboardButton("Check Membership", callback_data="check_membership")
            markup.add(join_button, check_button)
            bot.send_message(
                message.chat.id,
                "𝐉𝐨𝐢𝐧 𝐎𝐮𝐫 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐅𝐢𝐫𝐬𝐭 𝐓𝐨 𝐔𝐬𝐞 𝐓𝐡𝐞 𝐁𝐨𝐭",
                reply_markup=markup,
            )
    except Exception as e:
        logging.error(f"Error in start handler: {e}")

# Callback handler for "Check Membership" button
@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    try:
        if is_user_member(call.from_user.id):
            bot.answer_callback_query(call.id, "𝐉𝐨𝐢𝐧𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐘𝐨𝐮 𝐂𝐚𝐧 𝐏𝐫𝐨𝐜𝐞𝐞𝐝!✅")
            # Clear the "Join Channel" message
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # Send the welcome message
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "𝐘𝐨𝐮 𝐇𝐚𝐯𝐞𝐧'𝐭 𝐉𝐨𝐢𝐧𝐞𝐝 𝐎𝐮𝐫 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐘𝐞𝐭❌!")
    except Exception as e:
        logging.error(f"Error in check_membership callback: {e}")
        bot.answer_callback_query(call.id, "An error occurred. Please try again later.")

# Command to add a button (Admin only)
@bot.message_handler(commands=["add_button"])
def add_button(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "You are not authorized to perform this action.")
        return
    msg = bot.reply_to(message, "Send me the name of the new button.")
    bot.register_next_step_handler(msg, save_button_name)

def save_button_name(message):
    try:
        button_name = message.text
        if button_name in button_data:
            bot.reply_to(message, "Button already exists!")
        else:
            button_data[button_name] = {"file_id": None}
            save_data(button_data)
            bot.reply_to(
                message,
                f"Button '{button_name}' added! Now send a file to the private channel with this name as its caption.",
            )
    except Exception as e:
        logging.error(f"Error saving button name: {e}")

# Handle button press
@bot.message_handler(func=lambda message: message.text in button_data.keys())
def handle_button_press(message):
    try:
        if is_user_member(message.from_user.id):
            button_name = message.text
            file_id = button_data[button_name]["file_id"]

            if file_id:
                bot.send_document(message.chat.id, file_id)
            else:
                bot.reply_to(message, "The file is not yet assigned to this button.")
        else:
            bot.reply_to(message, "You need to join our channel to use this feature.")
    except Exception as e:
        logging.error(f"Error handling button press: {e}")

# Command to remove a button (Admin only)
@bot.message_handler(commands=["remove_button"])
def remove_button(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "You are not authorized to perform this action.")
        return
    if not button_data:
        bot.reply_to(message, "No buttons available to remove.")
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for button_name in button_data.keys():
        markup.add(KeyboardButton(button_name))

    msg = bot.send_message(
        message.chat.id,
        "Select the button you want to remove:",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, confirm_removal)

def confirm_removal(message):
    try:
        button_name = message.text
        if button_name in button_data:
            del button_data[button_name]
            save_data(button_data)
            bot.send_message(
                message.chat.id,
                f"Button '{button_name}' has been successfully removed.",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            bot.reply_to(message, "Invalid selection. Please use /remove_button again to select a valid button.")
    except Exception as e:
        logging.error(f"Error removing button: {e}")

# Listen for files in the private channel and save them
@bot.channel_post_handler(content_types=["document", "photo", "video", "audio"])
def save_file_from_channel(message):
    try:
        caption = message.caption or ""
        if caption in button_data and button_data[caption]["file_id"] is None:
            # Determine file ID based on the type of file
            file_id = None
            if message.document:
                file_id = message.document.file_id
            elif message.photo:
                file_id = message.photo[-1].file_id  # Get the highest-resolution photo
            elif message.video:
                file_id = message.video.file_id
            elif message.audio:
                file_id = message.audio.file_id

            if file_id:
                button_data[caption]["file_id"] = file_id
                save_data(button_data)
                bot.send_message(
                    PRIVATE_CHANNEL_ID,
                    f"File successfully saved for button '{caption}'.",
                )
    except Exception as e:
        logging.error(f"Error saving file from channel: {e}")

# Polling to keep the bot running
while True:
    try:
        bot.polling(none_stop=True, timeout=10, interval=0.1)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        sleep(5)
        