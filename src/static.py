from six.moves import configparser
from pymongo import MongoClient
from blinker import signal
import os
import sys

SETTINGS = {}

DB = None

SIGNAL_TELEGRAM = signal('TO_TELEGRAM')
SIGNAL_WHATSAPP = signal('TO_WHASTAPP')

def init_whatsapptelegram():
	conf_path = os.path.abspath(os.getenv('CONF',''))

	if not conf_path or not os.path.isfile(conf_path):
		sys.exit('No se pudo encontrar el archivo de configuracion')

	parser = configparser.ConfigParser()
	parser.read(conf_path)

	SETTINGS['whatsapp_phone'] = parser.get('whatsapp','phone')
	SETTINGS['whatsapp_password'] = parser.get('whatsapp','password')
	SETTINGS['owner_telegram'] = parser.getint('telegram','owner')
	SETTINGS['telegram_token'] = parser.get('telegram','token')

	DB = MongoClient(parser.get('db','path'))