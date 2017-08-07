import sys

from src.static import SETTINGS
from src.helper import get_contacto, get_numero
from src.telegram import tgrambot
from src.whatsapp import whatsappbot
from telebot import util as tgutil

def sigint_handler(signal, frame):
	sys.exit(0)

def to_telegram_handler(sender, **kwargs):
	numero = kwargs.get('numero')
	mensaje = kwargs.get('mensaje', '')

	contacto = get_contacto(numero)

	chat_id = SETTINGS['telegram_owner']

	if not contacto:
		output = "Mensaje para desconocido\n"
		output += 'Numero de telefono: %s\n' % numero
		output += '---------\n'
		output += mensaje
	else:
		output = "Mensaje para %s\n" % contacto
		output += '---------\n'
		output += mensaje

	for chunk in tgutil.split_string(output, 3000):
		tgrambot.send_message(chat_id, chunk)

def to_whatsapp_handler(sender, **kwargs):
	contacto = kwargs.get('contacto')
	mensaje = kwargs.get('mensaje')

	numero = get_numero(contacto)

	if not numero:
		tgrambot.send_message(
			SETTINGS['telegram_owner'],
			'Contacto desconocido: "%s"' % contacto
		)
		return

	whatsappbot.send_msg(phone=numero, message=mensaje)