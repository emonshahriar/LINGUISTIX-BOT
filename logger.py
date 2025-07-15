import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename="bot.log",
    filemode="a"
)

def log_error(update, context):
    logging.error(f"Update {update} caused error {context.error}")