import socket

from pyeznacl import SecretKey, CryptoString, PublicKey
from retval import RetVal, ErrEmptyData

from pyoganesson.wiremsg import WireMsg
from pyoganesson.packetsession import PacketSession

ErrSessionSetup = 'ErrSessionSetup'


def send_wire_error(msg_code: str, error_code: str, session: PacketSession) -> RetVal:
	'''Convenience function to quickly send an error response'''
	if not msg_code or not error_code:
		return RetVal(ErrEmptyData)
	
	wm = WireMsg(msg_code)
	wm.add_field('Error', error_code)
	return wm.write(session)


class OgServer:
	'''Handles the server side of an encrypted Oganesson messaging session'''

	def __init__(self, conn: socket.socket, fingerprint: str):
		self.session = PacketSession(conn)
		self.key = SecretKey()
		self.nextkey = None
		self.handlers = {}
		self.fingerprint = fingerprint		

	def Setup(self) -> RetVal:
		'''Handles the server side of setting up an encrypted comms channel with a client'''
		
		# Once the initial TCP connection is established, the client is expected to ask for the type
		# of session encryption expected. Anything else is an error.

		wm = WireMsg()
		status = wm.read(self.session)
		if status.error():
			return status
		
		if wm.code != 'SessionSetup':
			status = send_wire_error('SessionSetup', ErrSessionSetup, self.session)
			if status.error():
				return status
			return RetVal(ErrSessionSetup)
		
		wm.attachments = { 'Session':'og' }
		status = wm.write(self.session)
		if status.error():
			return status
		
		# A regular Og session is encrypted, but performs no identity checking. Setup consists of 
		# the client sending an ephemeral public key. The server receives it, generates a random 
		# XSalsa20 key, encrypts it, and sends it to the client.

		status = wm.read(self.session)
		if status.error():
			return status

		if wm.code != 'SessionKey' or not wm.has_field('PublicKey'):
			status = send_wire_error('SessionSetup', 'ErrProtocolError', self.session)
			if status.error():
				return status
			return RetVal(ErrSessionSetup)
		
		keycs = CryptoString(wm.attachments['PublicKey'])
		if not keycs.is_valid():
			status = send_wire_error('SessionSetup', 'ErrBadSessionKey', self.session)
			if status.error():
				return status
			return RetVal(ErrSessionSetup)

		pubkey = PublicKey(keycs)
		sessionkey = SecretKey()
		wm = WireMsg('SessionKey')
		wm.attachments['SecretKey'] = sessionkey.get_key()
		wm.attachments['Fingerprint'] = self.fingerprint
		status = wm.flatten()
		if status.error():
			send_wire_error('SessionSetup', 'ErrServerError', self.session)
			return status
		
		encmsg = pubkey.encrypt(status['bytes'])

		wm = WireMsg('SessionKey')
		wm.add_field('SessionKey', pubkey.public.prefix.encode() + ':' + encmsg, 'bytes')
		status = wm.write(self.session)

		# TODO: Implement OgServer server and client identity checking

		return status

# TODO: Continue implementing OgServer class
