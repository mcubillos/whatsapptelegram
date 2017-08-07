import telebot 

from src.static import SETTINGS, SIGNAL_WHATSAPP
from src.helper import db_agregar_contacto, db_lista_contactos, \
		db_eliminar_contacto, get_contacto, get_numero, cast_seguro

#bot
tgrambot = telebot.TeleBot(
	SETTINGS['telegram_token'],
	threaded= False,
	skip_pending=False
)

#handlers

@tgrambot.message_handler(commands=['start','help'])
def start(message):
	response = ('whatstelegram\n\n'
		    'Opciones:\n\n'
		    ' /ayuda -> Muestra este mensaje de ayuda\n'
		    ' /agregar <nombre> <numero> -> Agregar un nuevo contacto a la BD\n'
		    ' /contactos -> Lista de contactos\n'
		    ' /eliminar <nombre> -> Eliminar contacto de la BD\n'
		    ' /enviar <nombre> <mensaje> -> Enviar un mensaje al contacto de Whatsapp'
		   )
	tgrambot.reply_to(message,response)

@tgrambot.message_handler(commands=['yo'])
def yo(message):
	tgrambot.reply_to(message, message.chat.id)

@tgrambot.message_handler(commands=['agregar'])
def agregar_contacto(message):
	
	if message.chat.id != SETTINGS['owner_telegram']:
		tgrambot.reply_to(message, 'No eres el dueño de este bot')
		return
	
	args = telebot.util.extract_arguments(message.text)
	nombre, numero = args.split(maxsplit=1)

	if not nombre or not numero:
		tgrambot.reply_to(message,'Sintaxis /add <nombre> <numero>')
		return 

	if get_contacto(numero) or get_numero(nombre):
		tgrambot.reply_to(message, 'El contacto ya existe')
		return

	db_agregar_contacto(nombre, numero)

	tgrambot.reply_to(message, 'Contacto agregado')

@tgrambot.message_handler(commands=['contactos'])
def lista_contactos(message):
	if message.chat.id != SETTINGS['owner_telegram']:
		tgrambot.reply_to(message, 'No eres el dueño de este bot')
		return

	contactos = db_lista_contactos()

	response = 'Contactos:\n'
	for contacto in contactos:
		response += '- %s (%s)' % (contacto[0], contacto[1])
		response += '\n'

	tgrambot.reply_to(message, response)

@tgrambot.message_handler(commands=['eliminar'])
def eliminar_contacto(message):
	if message.chat.id != SETTINGS['owner_telegram']:
		tgrambot.reply_to(message, 'No eres el dueño de este bot')
		return

	nombre = telebot.util.extract_arguments(message.text)

	if not nombre:
		tgrambot.reply_to(message, 'Sintaxis: /eliminar <nombre>')
		return

	db_eliminar_contacto(nombre)

	tgrambot.reply_to(message, 'Contacto eliminado')

@tgrambot.message_handler(commands=['enviar'])
def enviar_whatsapp(message):
	if message.chat.id != SETTINGS['owner_telegram']:
		tgrambot.reply_to(message, 'No eres el dueño de este bot')
		return

	args = telebot.util.extract_arguments(message.text)
	nombre, mensaje = args.split(maxsplit=1)

	if not nombre or not mensaje:
		tgrambot.reply_to(message, 'Sintaxis: /send <nombre> <mensaje>')
		return

	SIGNAL_WHATSAPP.send('tgrambot', contacto=nombre, mensaje=mensaje) 


