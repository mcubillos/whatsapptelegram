from six.moves import configparser
from blinker import signal
import logging
import os
import sys

SETTINGS = {}

DB = None

SIGNAL_TELEGRAM = signal('TO_TELEGRAM')
SIGNAL_WHATSAPP = signal('TO_WHASTAPP')

def obtener_logger(name):
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)

	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)

	formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s[%(funcName)s]: %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	return logger

def init_whatsapptelegram():
	conf_path = os.path.abspath(os.getenv('WHATSAPPTELEGRAM_CONF',''))

	if not conf_path or not os.path.isfile(conf_path):
		sys.exit('No se pudo encontrar el archivo de configuracion')

	parser = configparser.ConfigParser()
	parser.read(conf_path)

	SETTINGS['whatsapp_phone'] = parser.get('whatsapp','phone')
	SETTINGS['whatsapp_password'] = parser.get('whatsapp','password')
	SETTINGS['owner_telegram'] = parser.getint('telegram','owner')
	SETTINGS['telegram_token'] = parser.get('telegram','token')