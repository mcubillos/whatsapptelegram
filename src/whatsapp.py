from yowsup.layers import YowLayerEvent
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities import OutgoingAckProtocolEntity
from yowsup.stacks import YowStackBuilder

from src.static import SETTINGS, SIGNAL_TELEGRAM

class WhatsappLayer(YowInterfaceLayer):
	@ProtocolEntityCallback('message')
	def on_message(self, message):
		sender = message.getFrom(full=False)

		receipt = OutgoingReceiptProtocolEntity(
			message.getId(),
			message.getFrom(),
			'read',
			message.getParticipant()
		)

		self.toLower(receipt)

		if message.getType() != 'text':
			return

		body = message.getBody()

		SIGNAL_TELEGRAM.send('whatsappbot', phone=sender, message=body)

	@ProtocolEntityCallback('receipt')
	def on_receipt(self, entity):
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
			return

		mensaje = kwargs.get('mensaje')

		entity = TextMessageProtocolEntity(
			mensaje,
			to='%s@s.whatsapp.net' % numero
		)

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