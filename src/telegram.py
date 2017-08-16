import telebot 

from src.static import SETTINGS, SIGNAL_WHATSAPP, obtener_logger

logger = obtener_logger('telegram')

#bot
tgrambot = telebot.TeleBot(
	SETTINGS['telegram_token'],
	threaded= False,
	skip_pending=False
)

#handlers

@tgrambot.message_handler(commands=['start','ayuda'])
def start(message):
	response = ('whatstelegram\n\n'
		    'Opciones:\n\n'
		    ' /ayuda -> Muestra este mensaje de ayuda\n'
		    ' /enviar <numero> <mensaje> -> Enviar un mensaje al numero de Whatsapp'
		   )
	tgrambot.reply_to(message,response)

@tgrambot.message_handler(commands=['yo'])
def yo(message):
	tgrambot.reply_to(message, message.chat.id)

@tgrambot.message_handler(commands=['enviar'])
def enviar_whatsapp(message):
	if message.chat.id != SETTINGS['owner_telegram']:
		tgrambot.reply_to(message, 'No eres el dueño de este bot')
		return

	args = telebot.util.extract_arguments(message.text)
	numero, mensaje = args.split(maxsplit=1)

	if not numero or not mensaje:
		tgrambot.reply_to(message, 'Sintaxis: /send <numero> <mensaje>')
		return

	logger.info('Reenviando a Whatsapp')
	SIGNAL_WHATSAPP.send('tgrambot', numero=numero, mensaje=mensaje) 


