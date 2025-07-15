from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from admin import upload_command, delete_command, is_admin
from db import get_resources, get_resource_by_id

SEMESTERS = {
    "1": ["Mathematics I", "Physics I"],
    "2": ["Mathematics II", "Chemistry"],
    "3": ["Mathematics III", "Biology"],
    "4": ["Mathematics IV", "Computer Science"],
    "5": ["Mathematics V", "Elective A"],
    "6": ["Mathematics VI", "Elective B"],
    "7": ["Project I", "Elective C"],
    "8": ["Project II", "Elective D"],
}
COURSE_RESOURCES = ["Books", "Past Questions", "Syllabus", "Notes"]

def start_keyboard():
    keyboard = [
        [InlineKeyboardButton(f"Semester {i}", callback_data=f"sem_{i}") for i in range(1, 9)],
        [InlineKeyboardButton("Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Select a semester:",
        reply_markup=start_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use the inline keyboard to browse resources.\n"
        "Admins: /upload to upload files, /delete to delete files."
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("sem_"):
        sem = data.split("_")[1]
        courses = SEMESTERS.get(sem, [])
        keyboard = [
            [InlineKeyboardButton(course, callback_data=f"course_{sem}_{i}")]
            for i, course in enumerate(courses)
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_start")])
        await query.edit_message_text(
            f"Semester {sem} Courses:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("course_"):
        _, sem, idx = data.split("_")
        course = SEMESTERS.get(sem, [])[int(idx)]
        keyboard = [
            [InlineKeyboardButton(res, callback_data=f"res_{sem}_{idx}_{res.lower()}")]
            for res in COURSE_RESOURCES
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data=f"sem_{sem}")])
        await query.edit_message_text(
            f"Course: {course}\nSelect Resource:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("res_"):
        _, sem, idx, res = data.split("_")
        course = SEMESTERS.get(sem, [])[int(idx)]
        resources = get_resources(sem, course, res)
        keyboard = [
            [InlineKeyboardButton(file_name, callback_data=f"file_{resource_id}")]
            for resource_id, file_name, file_id in resources
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data=f"course_{sem}_{idx}")])
        await query.edit_message_text(
            f"{res.title()} for {course}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("file_"):
        resource_id = data.split("_")[1]
        res = get_resource_by_id(resource_id)
        if res:
            file_id, file_name = res
            await query.message.reply_document(document=file_id, filename=file_name)
            await query.answer("File sent.", show_alert=False)
        else:
            await query.answer("File not found.", show_alert=True)

    elif data == "help":
        await query.edit_message_text("Help:\nUse the buttons to browse/download resources.\nAdmins: use /upload and /delete commands.")
    elif data == "back_to_start":
        await query.edit_message_text(
            "Select a semester:",
            reply_markup=start_keyboard()
        )

def setup_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CallbackQueryHandler(handle_callback))