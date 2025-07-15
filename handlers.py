from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from admin import upload_command, delete_command, is_admin
from db import get_resources, get_resource_by_id

SEMESTERS = {
    "1": [
        "UG1101 Introduction to Linguistics",
        "UG1102 Historical Linguistics",
        "UG1103 Academic Bangla",
        "UG1104 Academic English",
        "GEDC01 Sociology Anthropology"
    ],
    "2": [
        "UG1205 Morphology 1",
        "UG1206 Phonetics and Phonology 1",
        "UG1207 Writing System and Orthography",
        "GEDC02 ICT Fundamentals",
        "GEDC03 Psychology"
    ],
    "3": [
        "UG2301 Syntax 1",
        "UG2302 Semantics",
        "UG2303 Lexicology",
        "GEDC04 Bangla Literature"
    ],
    "4": [
        "UG2404 Morphology 2",
        "UG2405 Pragmatics",
        "UG2406 Sociolinguistics",
        "UG2407 Modern Schools of Linguistic Thought",
        "GEDN01 Leadership and Communication Development"
    ],
    "5": [
        "UG3501 Phonetics 2",
        "UG3502 Sign Language and Non-Verbal Communication",
        "UG3503 Semiotics and Communication Studies",
        "UG3504 Educational Linguistics",
        "GEDC05 Introduction to Statistics",
        "GEDC06 General Mathematics",
        "GEDN02 A Modern Language"
    ],
    "6": [
        "UG3605 Phonology 2",
        "UG3606 Research Methodology",
        "UG3607 Language Policy and Planning",
        "GEDC07 Bangla Literature 2",
        "GEDN03 Professional Ethics"
    ],
    "7": [
        "UG4701 Syntax 2",
        "UG4702 Language Documentation and Linguistic Field Methods",
        "UG4703 Stylistics",
        "GEDC08 Fundamentals of ICT"
    ],
    "8": [
        "UG4804 Psycholinguistics",
        "UG4805 Clinical Linguistics",
        "UG4806 Dialectology and Bangla Dialects",
        "GEDC09 Bangladesh Studies",
        "TC4810 Capstone Course/Thesis/Internship"
    ]
}
COURSE_RESOURCES = ["Books", "Past Questions", "Syllabus", "Notes"]

def start_keyboard():
    keyboard = [
        [InlineKeyboardButton(f"{i}", callback_data=f"sem_{i}") for i in range(1, 9)],
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
        "Use the inline keyboard to navigate through resources. Select semester, course, and the type of resource you want.\n"
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
            f"Course: {course}\n",
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
