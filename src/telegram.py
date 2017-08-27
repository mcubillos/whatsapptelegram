import telebot 
import requests
import time
import os

from src.static import SETTINGS, SIGNAL_WHATSAPP, obtener_logger

logger = obtener_logger('telegram')

#bot
tgrambot = telebot.TeleBot(
	SETTINGS['telegram_token'],
	threaded= False,
	skip_pending=False
)
knownUsers = []
userStep = {}

#handlers
def get_user_step(uid):
	if uid in userStep:
		return userStep[uid]
	else:
		knownUsers.append(uid)
		userStep[uid] = 0
		return 0

@tgrambot.message_handler(commands=['start','ayuda'])
def start(message):
	if message.chat.id not in knownUsers:
		knownUsers.append(message.chat.id)
		userStep[message.chat.id] = 0

	response = ('whatstelegram\n\n'
		    'Opciones:\n\n'
		    ' /ayuda -> Muestra este mensaje de ayuda\n'
		    ' /enviar <numero> <mensaje> -> Enviar un mensaje al numero de Whatsapp'
		    ' /foto <numero> foto -> Enviar foto al numero de Whatsapp'
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
		tgrambot.reply_to(message, 'Sintaxis: /enviar <numero> <mensaje>')
		return

	logger.info('Reenviando a Whatsapp')
	SIGNAL_WHATSAPP.send('tgrambot', numero=numero, mensaje=mensaje, is_media=False) 

@tgrambot.message_handler(commands=['foto'])
def enviar_whatsapp(message):
	if message.chat.id != SETTINGS['owner_telegram']:
		tgrambot.reply_to(message, 'No eres el dueño de este bot')
		return

	numero = telebot.util.extract_arguments(message.text)

	if not numero:
		tgrambot.reply_to(message, 'Sintaxis: /foto <numero>')
		return
	tgrambot.reply_to(message, 'Por favor seleccione su imagen ahora')
	time.sleep(15)
	updates = requests.get('https://api.telegram.org/bot'+SETTINGS['telegram_token']+'/getUpdates').json()
	file_id = updates['result'][-1]['message']['photo'][0]['file_id']
	last_file = requests.get('https://api.telegram.org/bot'+SETTINGS['telegram_token']+'/getFile?file_id='+file_id).json()
	logger.info(last_file)
	file_path = 'https://api.telegram.org/file/bot'+SETTINGS['telegram_token']+'/'+last_file['result']['file_path']
	file_name = (last_file['result']['file_path']).split('/')[1]
	logger.info(file_name)
	with open(file_name, 'wb') as fout:
		response = requests.get(file_path, stream=True)
		response.raise_for_status()
		for block in response.iter_content(4096):
			fout.write(block)
	ṕath = os.path.dirname(os.path.realpath(file_name))
	SIGNAL_WHATSAPP.send('tgrambot', numero=numero, mensaje=ṕath + '/' + file_name, is_media=True)