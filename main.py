import telebot
import decouple
import logging

config = decouple.Config('.env')

bot = telebot.TeleBot(config('TOKEN'))


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Hi")


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(e)
