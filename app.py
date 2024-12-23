# app.py

import telebot
from flask import Flask, request

# Для PDF
import fitz  # PyMuPDF
# Для EPUB
from ebooklib import epub, ITEM_DOCUMENT
# Для FB2 (можно также использовать lxml)
import xml.etree.ElementTree as ET

API_TOKEN = '7425060069:AAF-yOvLwG0jP8C6RXkaYIPh2dotUJxA_xo'  # <-- Вставьте сюда токен от BotFather (пример: 123456789:ABCDEFGH...)

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# -----------------------------
# 1. ФУНКЦИИ ДЛЯ ЧТЕНИЯ КНИГ
# -----------------------------

def process_pdf(file_path):
    """
    Извлекаем текст из PDF с помощью PyMuPDF.
    """
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def process_epub(file_path):
    """
    Извлекаем текст из EPUB-файла с помощью ebooklib.
    """
    book = epub.read_epub(file_path)
    text = ""
    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            content = item.get_content()
            text_part = content.decode('utf-8', errors='ignore')
            text += text_part
    return text

def process_fb2(file_path):
    """
    Извлекаем текст из FB2 (XML).
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    text = ""
    for elem in root.iter('p'):
        text += (elem.text or "") + "\n"
    return text

# -----------------------------
# 2. ОБРАБОТЧИКИ БОТА
# -----------------------------

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """
    При команде /start бот отправляет приветствие.
    """
    bot.send_message(
        message.chat.id,
        "Привет! Я BookReaderBot. "
        "Пришли мне книгу (PDF, EPUB, FB2), а я покажу её текст!"
    )

@bot.message_handler(content_types=['document'])
def handle_file(message):
    """
    Обработчик файлов. Определяем тип и извлекаем текст.
    """
    # 1. Получаем информацию о файле из Telegram
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = message.document.file_name.lower()

    # 2. Сохраняем файл на диск
    with open(file_name, 'wb') as f:
        f.write(downloaded_file)

    # 3. Определяем формат и обрабатываем
    if file_name.endswith('.pdf'):
        content = process_pdf(file_name)
    elif file_name.endswith('.epub'):
        content = process_epub(file_name)
    elif file_name.endswith('.fb2'):
        content = process_fb2(file_name)
    else:
        bot.reply_to(message, "Формат не поддерживается. Попробуйте PDF, EPUB или FB2.")
        return

    # 4. Если контент пуст — отправим уведомление, иначе результат
    if not content.strip():
        bot.send_message(
            message.chat.id,
            "Не удалось извлечь текст (возможно, файл пуст или это скан)."
        )
    else:
        # Ограничиваем ~4000 символов, так как Telegram имеет лимит ~4096
        bot.send_message(message.chat.id, content[:4000])

# -----------------------------
# 3. WEBHOOK: Веб-сервер Flask
# -----------------------------

@app.route('/', methods=['GET'])
def index():
    return "Привет! Я BookReaderBot (@MKFBookReaderBot). Бот-читалка."

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Здесь Telegram будет присылать новые сообщения (POST-запрос).
    """
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Unsupported content type", 400

# -----------------------------
# 4. ЗАПУСК ПРИЛОЖЕНИЯ
# -----------------------------
if __name__ == '__main__':
    # Для локального теста можно запускать Flask на порту 5000:
    app.run(host='0.0.0.0', port=5000)
