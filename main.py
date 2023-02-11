import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from decouple import config
import logging

from datetime import datetime, timedelta

logging.basicConfig(level=logging.WARNING)

bot = telebot.TeleBot(config('TOKEN'))
UTC_PLUS = config('UTC_PLUS', cast=int, default=0)


def smart_crop(img: Image.Image, width, height) -> Image.Image:
    if (width > img.width) or (height > img.height):
        k = max(width // img.width, height // img.height)
        res_img = img.resize(
            (img.width * k, img.height * k)
        )
        a, b = (res_img.width - width) // 2, (res_img.height - height) // 2
        crop_img = res_img.crop((a, b, res_img.width - a, res_img.height - b))

        final_img = crop_img.resize(
            (width, height)
        )
    else:
        k = min(img.width // width, img.height // height)
        res_img = img.resize(
            (img.width // k, img.height // k)
        )
        a, b = (res_img.width - width) // 2, (res_img.height - height) // 2
        crop_img = res_img.crop((a, b, res_img.width - a, res_img.height - b))
        final_img = crop_img.resize(
            (width, height)
        )

    return final_img


def generate_image(template_number: int, name: str, price: float, product_image: Image, url: str) -> Image:
    def create_qr_code(url: str, logo: Image) -> bytes:
        qr = qrcode.QRCode(
            version=5,
            error_correction=2,
            box_size=10,
            border=0,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img: Image.Image = img.get_image()
        img = img.convert('RGBA')
        img_width, img_height = img.size

        logo = logo.resize((int(img_height / 3.2), int(img_height / 3.2)))
        logo_width, logo_height = logo.size
        img.paste(logo, (img_width // 2 - logo_width // 2, img_height // 2 - logo_height // 2))

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return img_io.read()

    template = ['images/MY.png', 'images/PH.png', 'images/SG.png'][template_number]
    template = Image.open(template)
    template_width, template_height = template.size

    price_text = f"{price} {['MYR', 'PHP', 'SGD'][template_number]}"
    draw = ImageDraw.Draw(template)

    # Draw time
    time_font = ImageFont.truetype('fonts/SFProText-Semibold.ttf', 50)
    time_ = datetime.utcnow() + timedelta(hours=UTC_PLUS)
    time_text = time_.strftime('%H:%M')
    _, _, text_width, text_height = draw.textbbox((0, 0), time_text, font=time_font)
    draw.text((120, 50), time_text, fill='black', font=time_font)

    # Draw product name
    name_font = ImageFont.truetype('fonts/SFProText-Semibold.ttf', 70)

    _, _, text_width, text_height = draw.textbbox((0, 0), name, font=name_font)
    draw.text((int((template.width - text_width) / 2), 680), name, fill='#686968', font=name_font)

    # Draw product price
    price_font = ImageFont.truetype('fonts/SFProText-Semibold.ttf', 60)

    _, _, text_width, text_height = draw.textbbox((0, 0), price_text, font=price_font)
    draw.text((530, 1332), price_text, fill='#db242d', font=price_font)

    # Paste product image
    product_width, product_height = product_image.size

    PRODUCT_IMAGE_WEIGHT = 0.6 * template_width
    PRODUCT_IMAGE_HEIGHT = 0.2 * template_height
    PRODUCT_IMAGE_WEIGHT, PRODUCT_IMAGE_HEIGHT = int(PRODUCT_IMAGE_WEIGHT), int(PRODUCT_IMAGE_HEIGHT)

    product_image = smart_crop(product_image, PRODUCT_IMAGE_WEIGHT, PRODUCT_IMAGE_HEIGHT)

    template.paste(product_image, (int(template_width / 2 - product_image.size[0] / 2), 780))

    # Draw watermark
    watermark = Image.open('images/watermark.png')
    watermark_width, watermark_height = watermark.size
    new_width = 176 / 805 * template_width
    new_height = watermark_height / watermark_width * new_width
    new_width, new_height = int(new_width), int(new_height)
    watermark = watermark.resize((new_width, new_height))

    template.paste(watermark, (250, 1215), watermark)

    # Paste QR code
    qr_code = Image.open(BytesIO(create_qr_code(url, Image.open('images/logo.png'))))
    qr_code = qr_code.resize((int(template_width * 0.5), int(template_width * 0.5)))
    template.paste(qr_code,
                   (int(template_width / 2 - qr_code.size[0] / 2), int(template_height * 0.68 - qr_code.size[1] / 2)))

    return template


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Отправьте /generate для генерации скриншота")


def generate_handler_image_step(message, template_number, name, price, url):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = Image.open(BytesIO(downloaded_file))
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при загрузке фото. Попробуйте еще раз")
        bot.register_next_step_handler(message, generate_handler_image_step, template_number, name, price, url)
        return
    try:
        img_io = BytesIO()
        generate_image(template_number, name, price, src, url).save(img_io, 'PNG')
        img_io.seek(0)
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при генерации скриншота. Попробуйте еще раз")
        bot.register_next_step_handler(message, generate_handler_image_step, template_number, name, price, url)
        return
    bot.send_photo(message.chat.id, img_io, caption="Скриншот готов! Чтобы сгенерировать еще один, отправьте /generate")


def generate_handler_url_step(message, template_number, name, price):
    url = message.text
    bot.send_message(message.chat.id, "Отправьте фото товара:")
    bot.register_next_step_handler(message, generate_handler_image_step, template_number, name, price, url)


def generate_handler_price_step(message, template_number, name):
    try:
        price = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Цена должна быть числом")
        bot.register_next_step_handler(message, generate_handler_price_step, template_number, name)
        return

    bot.send_message(message.chat.id, "Ссылка на товар:")
    bot.register_next_step_handler(message, generate_handler_url_step, template_number, name, price)


def generate_handler_name_step(message, template_number):
    name = message.text
    bot.send_message(message.chat.id, "Цена товара:")
    bot.register_next_step_handler(message, generate_handler_price_step, template_number, name)


choose_template_keyboard = InlineKeyboardMarkup()
choose_template_keyboard.add(
    InlineKeyboardButton(text="Шаблон MY", callback_data=f"template:0"))
choose_template_keyboard.add(
    InlineKeyboardButton(text="Шаблон PH", callback_data=f"template:1"))
choose_template_keyboard.add(
    InlineKeyboardButton(text="Шаблон SG", callback_data="template:2"))


@bot.message_handler(commands=['generate'])
def generate_handler(message):
    bot.send_message(message.chat.id, "Выберите шаблон:", reply_markup=choose_template_keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: telebot.types.CallbackQuery):
    if call.data.startswith('template:'):
        template_number = int(call.data.split(':')[1])
        bot.edit_message_text("Название товара:", call.message.chat.id, call.message.id)
        bot.register_next_step_handler(call.message, generate_handler_name_step, template_number)


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(e)
