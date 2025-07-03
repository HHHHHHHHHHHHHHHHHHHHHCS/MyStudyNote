from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os

async def release(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("开始发布版本...")
	print("!!!!!")
	# os.system("bash ./release.sh")  # 替换为你的构建脚本路径

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text
	await update.message.reply_text("收到，马上开始发布版本！")
	print(text)


def luanch_bot(token):
	if token is None:
		print("Token is none")
		return

	app = ApplicationBuilder().token(token).build()
	app.add_handler(CommandHandler("release", release))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

	print("Run robot!")
	app.run_polling()

if __name__ == '__main__':
	with open("Token.ini", "r", encoding="utf-8") as file:
		token = file.read().strip()
		luanch_bot(token)


