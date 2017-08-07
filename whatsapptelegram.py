from __future__ import print_function

import signal
import threading

from src.static import SIGNAL_TELEGRAM, SIGNAL_WHATSAPP, init_whatsapptelegram

init_whatsapptelegram()

from src.listeners import telegram_listener, whatsapp_listener
from src.signals import sigint_handler, to_telegram_handler, to_whatsapp_handler

if __name__ == '__main__':
	signal.signal(signal.SIGINT, sigint_handler)
	print('Presionar Ctrl+C para salir')

	SIGNAL_TELEGRAM.connect(to_telegram_handler)
	SIGNAL_WHATSAPP.connect(to_whatsapp_handler)

	telegram_thread = threading.Thread(target=telegram_listener)
	whastsapp_thread = threading.Thread(target=whatsapp_listener)

	telegram_thread.start()
	whastsapp_thread.start()

	telegram_thread.join()
	whastsapp_thread.join()

