from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from db import add_resource, delete_resource

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