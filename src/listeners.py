import time
from src.static import obtener_logger
from src.telegram import tgrambot
from src.whatsapp import WHATSAPP_STACK, _connect_signal

logger = obtener_logger('listeners')

def telegram_listener():
	while True:
		try:
			logger.info('Empezando Telegram listener')
			tgrambot.polling(none_stop=True)

		except Exception as e:
			logger.error(e)
			time.sleep(10)
			pass
		logger.info('Se detuvo el listener de Telegram')
		tgrambot.stop_polling()

def whatsapp_listener():
	while True:
		try:
			logger.info('Empezando Whatsapp listener')
			WHATSAPP_STACK.broadcastEvent(_connect_signal)
			WHATSAPP_STACK.loop()

		except Exception as e:
			logger.error(e)
			time.sleep(10)
			pass