from yowsup.layers import YowLayerEvent
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.protocol_messages.protocolentities import *
from yowsup.layers.protocol_ib.protocolentities import *
from yowsup.layers.protocol_iq.protocolentities import *
from yowsup.layers.protocol_receipts.protocolentities import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities import OutgoingAckProtocolEntity
from yowsup.layers.protocol_media.protocolentities import * #media
from yowsup.layers.protocol_media.mediauploader import MediaUploader # media
from yowsup.common.tools import Jid
from yowsup.stacks import YowStackBuilder

import os
import threading
import sys
import io
from PIL import Image

from src.static import SETTINGS, SIGNAL_TELEGRAM, obtener_logger

logger = obtener_logger('whatsapp')

EXT_IMAGE = ['.jpg', '.png']
EXT_AUDIO = ['.mp3', '.wav', '.aac', '.wma']
EXT_VIDEO = ['.mp4']

class WhatsappLayer(YowInterfaceLayer):
	def __init__(self):
		super(WhatsappLayer, self).__init__()
		self.ackQueue = []
		self.lock = threading.Condition()

	def get_upload_entity(self,path):
		filename, extension = os.path.splitext(path)
		logger.info(extension)
		if extension in EXT_IMAGE:
			return RequestUploadIqProtocolEntity(
				RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, filePath = path
			)
		if extension in EXT_VIDEO:
			return RequestUploadIqProtocolEntity(
				RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO, filePath = path
			)
		if extension in EXT_AUDIO:
			return RequestUploadIqProtocolEntity(
				RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO, filePath = path
			)
		self.disconnect("ERROR MEDIA")		

	@ProtocolEntityCallback('message')
	def on_message(self, message):
		numero = message.getFrom(full=False)

		logger.debug('Se recibio mensaje de %s' % numero)

		receipt = OutgoingReceiptProtocolEntity(
			message.getId(),
			message.getFrom(),
			'read',
			message.getParticipant()
		)

		self.toLower(receipt)

		if message.getType() == 'text':
			mensaje = message.getBody()
			messageForSend = mensaje.encode('latin-1').decode() if sys.version_info >= (3,0) else mensaje
			logger.info('Reenviando mensaje a Telegram')
			SIGNAL_TELEGRAM.send('whatsappbot', numero=numero, mensaje=messageForSend, is_media=False)
		elif message.getType() == 'media' :
			if message.getMediaType() in ("image", "audio", "video"):
				file_name = message.getMediaUrl().decode("utf-8").split('/d/f/')[1].split('.')[0]
				ext = message.getExtension()

				mediaContent = message.getMediaContent()
				image = Image.open(io.BytesIO(mediaContent))
				image.save(file_name+ext)

				path = os.path.dirname(os.path.realpath(file_name+ext))
				imagenUrl = path +"/"+ file_name + ext

				logger.info('Reenviando imagen a Telegram')
				SIGNAL_TELEGRAM.send('whatsappbot', numero=numero, mensaje=imagenUrl, is_media=True)
			else:
				logger.info('[Tipo de media: %s]' % message.getMediaType())
		else:
			logger.info('No se conoce el tipo de mensaje %s' % message.getType())

	@ProtocolEntityCallback('receipt')
	def on_receipt(self, entity):
		logger.debug('Mensaje ACK')
		ack = OutgoingAckProtocolEntity(
			entity.getId(),
			'receipt',
			entity.getType(),
			entity.getFrom()
		)
		self.toLower(ack)

	def send_msg(self, **kwargs):
		self.lock.acquire()
		numero = kwargs.get('numero')

		if not numero:
			logger.debug('No se proporciono numero de telefono')
			return

		mensaje = kwargs.get('mensaje')
		is_media = kwargs.get('is_media')
		
		jid = "%s@s.whatsapp.net" % numero
		
		if is_media:
			path = mensaje
			entidad = self.get_upload_entity(path)
			logger.info(entidad)
			success_fn = lambda success, original: self.on_request_upload_result(jid, path, success, original,caption)
			error_fn = lambda error, original: self.on_request_upload_error(jid,path,error,original)
			self._sendIq(entidad, success_fn, error_fn)
		else:
			entidad_mensaje = TextMessageProtocolEntity(mensaje,to=jid)
			self.ackQueue.append(entidad_mensaje.getId())
			self.toLower(entidad_mensaje)
		self.lock.release()
	
	def disconnect(self, result=None):
		self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
		if result:
			raise ValueError(result)

	def on_request_upload_result(self, jid, file_path, result_entity, request_entity, caption=None):
		logger.info("Estoy en el upload")
		if result_entity.isDuplicate():
			self.send_file(file_path, result_entity.getUrl(), jid, result_entity.getIp())
		else:
			uploader = MediaUploader(
				jid, self.getOwnJid(),
				file_path,
				result_entity.getUrl(),
				result_entity.getResumeOffset(),
				self.on_upload_success,
				self.on_upload_error,
				self.on_upload_progress,
				async=False
			)
			uploader.start()

	def on_request_upload_error(self, jid, file_path, error_entity, original_entity):
		logger.info(file_path)
		logger.info(error_entity)
		self.disconnect("ERROR REQUEST")

	def on_upload_error(self, file_path, jid, url):
		self.disconnect("ERROR UPLOAD")

	def on_upload_success(self, file_path, jid, url):
		logger.info("Hola estoy en el upload")
		self.send_file(file_path, url, jid)

	def on_upload_progress(self, file_path, jid, url, progress):
		logger.info("Progress: {}".format(progress))

	def send_file(self, file_path, url, to, ip=None):
		filename, extension = os.path.splitext(file_path)
		entity = None
		logger.info(file_path)
		if extension in EXT_IMAGE:
			entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip,to, caption =caption)
		elif extension in EXT_VIDEO:
			entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to, caption =caption)
		elif extension in EXT_AUDIO:
			entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to)
		self.toLower(entity)
	
whatsappbot = WhatsappLayer()

_connect_signal = YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT)

WHATSAPP_STACK = (
	YowStackBuilder()
	.pushDefaultLayers(True)
	.push(whatsappbot)
	.build()
)

WHATSAPP_STACK.setCredentials((SETTINGS['whatsapp_phone'], SETTINGS['whatsapp_password']))