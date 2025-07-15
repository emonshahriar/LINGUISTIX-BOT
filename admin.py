from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from db import add_resource, delete_resource
from db import get_resource_by_id

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Unauthorized. Only admins can upload files.")
        return

    if update.message.reply_to_message and update.message.reply_to_message.document:
        doc = update.message.reply_to_message.document
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Usage: /upload <semester> <course> <resource_type>")
            return
        semester, course, resource_type = args[0], args[1], args[2]
        add_resource(semester, course, resource_type, doc.file_id, doc.file_name, user_id)
        await update.message.reply_text(f"File '{doc.file_name}' uploaded and saved to database.")
    else:
        await update.message.reply_text(
            "Reply to a file with /upload <semester> <course> <resource_type> to upload and save metadata."
        )

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Unauthorized. Only admins can delete files.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /delete <resource_id>")
        return

    delete_resource(args[0])
    await update.message.reply_text(f"Resource with ID {args[0]} deleted from database.")

# Inline upload handler for admins (used in inline upload flow)
async def inline_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Unauthorized. Only admins can upload files.")
        return

    doc = update.message.document
    semester = context.user_data.get("upload_semester")
    course = context.user_data.get("upload_course")
    resource_type = context.user_data.get("upload_resource_type")
    if not all([semester, course, resource_type, doc]):
        await update.message.reply_text("Missing upload context. Please restart the upload from the course menu.")
        return

    add_resource(semester, course, resource_type, doc.file_id, doc.file_name, user_id)
    await update.message.reply_text(f"File '{doc.file_name}' uploaded and saved to database for {course} ({resource_type}).")

# Inline delete handler for admins (used in inline delete flow)
async def inline_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, resource_id):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.callback_query.edit_message_text("Unauthorized. Only admins can delete files.")
        return

    # Confirm resource exists
    res = get_resource_by_id(resource_id)
    if not res:
        await update.callback_query.edit_message_text("Resource not found. Already deleted?")
        return

    delete_resource(resource_id)
    await update.callback_query.edit_message_text(f"Resource with ID {resource_id} deleted from database.")
