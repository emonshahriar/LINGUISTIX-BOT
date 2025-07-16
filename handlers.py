from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
)
from admin import is_admin, inline_upload_handler, inline_delete_handler
from db import get_resources, get_resource_by_id

HELP_MESSAGE = (
    "Use the buttons to navigate through the resources. "
    "Select the semester, course and the resource type you are looking for. "
    "Use /start to initiate."
)

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
    await update.message.reply_text(HELP_MESSAGE)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

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
        # Add Upload button for admins
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("Upload Resource", callback_data=f"upload_{sem}_{idx}")])
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
            + ([InlineKeyboardButton("Delete", callback_data=f"delete_{resource_id}")] if is_admin(user_id) else [])
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

    elif data.startswith("upload_"):
        # Admin pressed "Upload Resource"
        _, sem, idx = data.split("_")
        # Save context for upload flow
        context.user_data["upload_semester"] = sem
        context.user_data["upload_course"] = SEMESTERS.get(sem, [])[int(idx)]
        # Ask for resource type
        keyboard = [
            [InlineKeyboardButton(res, callback_data=f"uploadtype_{res.lower()}")]
            for res in COURSE_RESOURCES
        ]
        await query.edit_message_text(
            "Select resource type to upload:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("uploadtype_"):
        # Resource type selected, ask for file
        resource_type = data.split("_")[1]
        context.user_data["upload_resource_type"] = resource_type
        await query.edit_message_text(
            f"Send the file you want to upload for {context.user_data['upload_course']} ({resource_type})."
        )
        # Set a flag to handle next document message
        context.user_data["awaiting_file_upload"] = True

    elif data.startswith("delete_"):
        # Admin pressed Delete for a resource
        resource_id = data.split("_")[1]
        context.user_data["delete_resource_id"] = resource_id
        # Ask for confirmation
        keyboard = [
            [InlineKeyboardButton("Confirm Delete", callback_data=f"confirmdelete_{resource_id}")],
            [InlineKeyboardButton("Cancel", callback_data=f"canceldelete_{resource_id}")]
        ]
        await query.edit_message_text(
            "Are you sure you want to delete this resource?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("confirmdelete_"):
        # Actually delete
        resource_id = data.split("_")[1]
        await inline_delete_handler(update, context, resource_id)
    elif data.startswith("canceldelete_"):
        await query.edit_message_text("Delete cancelled.")

    elif data == "help":
        await query.edit_message_text(HELP_MESSAGE)
    elif data == "back_to_start":
        await query.edit_message_text(
            "Select a semester:",
            reply_markup=start_keyboard()
        )

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle inline upload flow for admins
    if context.user_data.get("awaiting_file_upload"):
        await inline_upload_handler(update, context)
        context.user_data["awaiting_file_upload"] = False

def setup_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
