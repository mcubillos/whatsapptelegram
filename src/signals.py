import sys

from src.static import SETTINGS, obtener_logger
from src.telegram import tgrambot
from src.whatsapp import whatsappbot
from telebot import util as tgutil

logger = obtener_logger('signals')

def sigint_handler(signal, frame):
	sys.exit(0)

def to_telegram_handler(sender, **kwargs):
	numero = kwargs.get('numero')
	mensaje = kwargs.get('mensaje', "")
	is_media = kwargs.get('is_media')

	chat_id = SETTINGS['owner_telegram']
	if is_media:
		try:
			with open(mensaje) as file:
				tgrambot.send_photo(chat_id, file)
		except FileNotFoundError:
			logger.info("Error con el archivo")

	output = "Mensaje de %s\n" % numero
	output += '---------\n'
	output += mensaje
	logger.info('Mensaje recibido de %s' % numero)

	for chunk in tgutil.split_string(output, 3000):
		tgrambot.send_message(chat_id, chunk)

def to_whatsapp_handler(sender, **kwargs):
	numero = kwargs.get('numero')
	mensaje = kwargs.get('mensaje', "")
	is_media = kwargs.get('is_media')

	if not numero:
		tgrambot.send_message(
			SETTINGS['owner_telegram'],
			'No se envio numero'
		)
		return

	logger.info('Enviando mensaje para %s' % numero)
	whatsappbot.send_msg(numero=numero, mensaje=mensaje, is_media=is_media)