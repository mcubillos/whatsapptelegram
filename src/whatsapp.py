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
			path, extension = os.path.splitext(mensaje)

			if extension in EXT_IMAGE:
				mediaType =  RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE
			if extension in EXT_VIDEO:
				mediaType = RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO
			if extension in EXT_AUDIO:
				mediaType = RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO

			entity = RequestUploadIqProtocolEntity(mediaType, filePath=mensaje)
			successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, mediaType, mensaje, successEntity, originalEntity)
			errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, mensaje, errorEntity, originalEntity)
			self._sendIq(entity, successFn, errorFn)
		else:
			entidad_mensaje = TextMessageProtocolEntity(mensaje,to=jid)
			self.ackQueue.append(entidad_mensaje.getId())
			self.toLower(entidad_mensaje)
		self.lock.release()
	
	def disconnect(self, result=None):
		self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
		if result:
			raise ValueError(result)

	def doSendMedia(self, mediaType, filePath, url, to, ip = None, caption = None):
		if mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE:
			entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
		elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
			entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to)
		elif mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO:
			entity = VideoDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
		self.toLower(entity)

	def onRequestUploadResult(self, jid, mediaType, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):

		if resultRequestUploadIqProtocolEntity.isDuplicate():
			self.doSendMedia(mediaType, filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid,
							 resultRequestUploadIqProtocolEntity.getIp(), caption)
		else:
			successFn = lambda filePath, jid, url: self.doSendMedia(mediaType, filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
			mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
									  resultRequestUploadIqProtocolEntity.getUrl(),
									  resultRequestUploadIqProtocolEntity.getResumeOffset(),
									  successFn, self.onUploadError, self.onUploadProgress, async=False)
			mediaUploader.start()

	def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
		logger.error("Request upload for file %s for %s failed" % (path, jid))

	def onUploadError(self, filePath, jid, url):
		logger.error("Upload file %s to %s for %s failed!" % (filePath, url, jid))

	def onUploadProgress(self, filePath, jid, url, progress):
		sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
		sys.stdout.flush()

whatsappbot = WhatsappLayer()

_connect_signal = YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT)

WHATSAPP_STACK = (
	YowStackBuilder()
	.pushDefaultLayers(True)
	.push(whatsappbot)
	.build()
)

WHATSAPP_STACK.setCredentials((SETTINGS['whatsapp_phone'], SETTINGS['whatsapp_password']))