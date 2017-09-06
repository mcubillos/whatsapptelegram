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

from src.static import SETTINGS, SIGNAL_TELEGRAM, obtener_logger

logger = obtener_logger('whatsapp')

EXT_IMAGE = ['.jpg', '.png']
EXT_AUDIO = ['.mp3', '.wav', '.aac', '.wma']
EXT_VIDEO = ['.mp4']

class WhatsappLayer(YowInterfaceLayer):
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
			logger.info('Reenviando mensaje a Telegram')
			SIGNAL_TELEGRAM.send('whatsappbot', numero=numero, mensaje=mensaje, is_media=False)
		elif message.getType() == 'media' :
			if message.getMediaType() in ("image","audio","video"):
				imagenUrl = message.getMediaUrl()
				logger.info('Reenviando imagen a Telegram')
				SIGNAL_TELEGRAM.send('whatsappbot', numero=numero, mensaje=imagenUrl, is_media=True)
			elif message.getMediaType() == 'location':
				logger.info('Reenviando locacion a Telegram')

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
			success_fn = lambda success, original:self.on_request_upload_result(jid, path, success, original)
			error_fn = lambda error, original: self.on_request_upload_error(jid,path,error,original)
			self._sendIq(entidad,success_fn,error_fn)
		else:
			entidad_mensaje = TextMessageProtocolEntity(mensaje,to=jid)
			self.toLower(entidad_mensaje)
	
	def disconnect(self, result=None):
		self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
		if result:
			raise ValueError(result)

	def on_request_upload_result(self, jid, file_path, result_entity, request_entity):
		logger.info(file_path)
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

	def on_request_upload_error(self,*args):
		logger.info(*args)
		self.disconnect("ERROR REQUEST")

	def on_upload_error(self, file_path, jid, url):
		self.disconnect("ERROR UPLOAD")

	def on_upload_success(self, file_path, jid, url):
		self.send_file(file_path, url, jid)

	def on_upload_progress(self, file_path, jid, url, progress):
		logger.info("Progress: {}".format(progress))

	def send_file(self, file_path, url, to, ip=None):
		filename, extension = os.path.splitext(file_path)
		entity = None
		logger.info(file_path)
		if extension in EXT_IMAGE:
			entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip,to)
			self.toLower(entity)
		elif extension in EXT_VIDEO:
			entity = DownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, "video", ip, to)
			self.toLower(entity)
		elif extension in EXT_AUDIO:
			entity = DownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, "audio", ip, to)
			self.toLower(entity)
		if entity:
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