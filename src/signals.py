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
	mensaje = kwargs.get('mensaje', '')

	chat_id = SETTINGS['owner_telegram']

	output = "Mensaje para %s\n" % numero
	output += '---------\n'
	output += mensaje
	logger.info('Mensaje recibido para %s' % numero)

	for chunk in tgutil.split_string(output, 3000):
		tgrambot.send_message(chat_id, chunk)

def to_whatsapp_handler(sender, **kwargs):
	numero = kwargs.get('numero')
	mensaje = kwargs.get('mensaje')

	if not numero:
		tgrambot.send_message(
			SETTINGS['owner_telegram'],
			'Numero desconocido: "%s"' % numero
		)
		return

	logger.info('Enviando mensaje para %s' % numero)
	whatsappbot.send_msg(numero=numero, mensaje=mensaje)