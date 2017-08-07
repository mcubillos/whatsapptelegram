import time

from src.telegram import tgrambot
from src.whatsapp import WHATSAPP_STACK, _connect_signal

def telegram_listener():
	while True:
		try:
			tgrambot.polling(none_stop=True)

		except Exception as e:
			time.sleep(10)
			pass
		tgrambot.stop_polling()

def whatsapp_listener():
	while True:
		try:
			WHATSAPP_STACK.broadcastEvent(_connect_signal)
			WHATSAPP_STACK.loop()

		except Exception as e:
			time.sleep(10)
			pass