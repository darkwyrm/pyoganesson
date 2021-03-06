from base64 import b85encode
import secrets
import socket

from pyeznacl import SecretKey, CryptoString, PublicKey, EncryptionPair
from retval import RetVal, ErrEmptyData, ErrClientError, ErrServerError

from pyoganesson.wiremsg import WireMsg, ErrInvalidMsg
from pyoganesson.packetsession import PacketSession

ErrSessionSetup = 'ErrSessionSetup'
ErrKeyError = 'ErrKeyError'
ErrSessionMismatch = 'ErrSessionMismatch'


def send_wire_error(msg_code: str, error_code: str, session: PacketSession) -> RetVal:
	'''Convenience function to quickly send an error response'''
	if not msg_code or not error_code:
		return RetVal(ErrEmptyData)
	
	wm = WireMsg(msg_code)
	wm.attachments['Error'] = error_code
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

		if wm.code != 'SessionKey' or 'PublicKey' not in wm.attachments:
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
		wm.attachments['SessionKey'] = pubkey.public.prefix.encode() + b':' + encmsg['data']
		status = wm.write(self.session)

		# TODO: Implement OgServer server and client identity checking

		return status

	def read_data(self) -> RetVal:
		'''Reads raw byte data from the network connection.
		
		Notes:
		Like working with a raw socket, the contents don't matter, but they do have to fit within 
		system memory.
		'''

		wm = WireMsg()
		status = wm.read(self.session)
		if status.error():
			return status
		
		if wm.code != 'OgMsg' or 'Payload' not in wm.attachments:
			return RetVal(ErrClientError)

		status = self.key.decrypt(wm.attachments['Payload'])
		if status.error():
			return status
		
		status = wm.unflatten(status['data'])
		if status.error():
			return status

		if 'Data' not in wm.attachments or 'NextKey' not in wm.attachments:
			return RetVal(ErrInvalidMsg)
		
		next_key_str = CryptoString(wm.attachments['NextKey'])
		if not next_key_str.is_valid():
			return RetVal(ErrKeyError)
		
		self.nextkey = SecretKey(next_key_str)

		return wm.attachments['Data']

	def write_data(self, data: bytes) -> RetVal:
		'''Writes raw byte data to the network connection'''

		if not data:
			return RetVal(ErrEmptyData)
		
		wm = WireMsg('EncMsg')
		wm.attachments['Data'] = data
		padding = secrets.token_bytes(secrets.randbelow(16)+1)
		wm.attachments['Padding'] = str(b85encode(padding))
		wm.attachments['NextKey'] = self.nextkey.as_string()

		status = wm.flatten()
		if status.error():
			return status
		
		status = self.key.encrypt(status['bytes'])
		if status.error():
			return status
		
		wrapper = WireMsg('OgMsg')
		wrapper.attachments['Payload'] = status['data']
		status = wrapper.write(self.session)
		if status.error():
			return status
		
		self.key = self.nextkey

		return RetVal()


class OgClient:
	'''Handles the client side of an encrypted Oganesson messaging session'''

	def __init__(self, conn: socket.socket, fingerprint: str, serverfp: str):
		self.session = PacketSession(conn)
		self.key = None
		self.nextkey = None
		self.handlers = {}
		self.fingerprint = fingerprint
		self.serverfp = serverfp

	def Setup(self) -> RetVal:
		'''Handles the server side of setting up an encrypted comms channel with a client'''

		wm = WireMsg('SessionSetup')
		status = wm.write(self.session)
		if status.error():
			return status
		
		status = wm.read(self.session)
		if status.error():
			return status
		
		if wm.code != 'SessionSetup':
			return RetVal(ErrSessionSetup, 'incorrect server session query response')
		if 'Error' in wm.attachments:
			return RetVal(wm.attachments['Error'])
		if 'Session' not in wm.attachments:
			return RetVal(ErrServerError, 'setup response missing Session field')
		if wm.attachments['Session'] != 'og':
			return RetVal(ErrSessionMismatch, 
				f"Expected 'og' response, got '{wm.attachments['Session']}'")
		
		# A regular Og session is encrypted, but performs no identity checking. Setup consists of 
		# the client sending an ephemeral public key. The server receives it, generates a random 
		# XSalsa20 key, encrypts it, and sends it to the client.

		keypair = EncryptionPair()
		if not keypair.is_valid():
			return RetVal(ErrKeyError)
		
		wm = WireMsg('SessionKey')
		wm.attachments['PublicKey'] = keypair.get_public_key()

		if self.fingerprint:
			wm.attachments['Fingerprint'] = self.fingerprint
		
		status = wm.write(self.session)
		if status.error():
			return status
		
		status = wm.read(self.session)
		if status.error():
			return status
		
		if wm.code != 'SessionKey':
			return RetVal(ErrSessionSetup, 
				f"expected response code 'SessionKey' from server, got '{wm.code}'")
		if 'Error' in wm.attachments:
			return RetVal(wm.attachments['Error'])
		if 'SessionKey' not in wm.attachments:
			return RetVal(ErrServerError, 'server did not respond with session key')

		enc_keystr = CryptoString(wm.attachments['SessionKey'])
		if not enc_keystr.is_valid():
			return RetVal(ErrServerError)
		status = keypair.decrypt(enc_keystr.data)
		if status.error():
			return status
		
		wm = WireMsg()
		status = wm.unflatten(status['data'])
		if status.error():
			return status
		if 'SecretKey' not in wm.attachments or 'Fingerprint' not in wm.attachments:
			return RetVal(ErrServerError, 'server failed to return key and fingerprint')

		key_cs = CryptoString(wm.attachments['SecretKey'])
		if not key_cs.is_valid():
			return RetVal(ErrKeyError, 'server returned invalid session key')
		self.key = SecretKey(key_cs)
		self.serverfp = wm.attachments['Fingerprint']

		# TODO: Implement OgClient server and client identity checking
		
		return RetVal()
		
	def read_data(self) -> RetVal:
		'''Reads raw byte data from the network connection.
		
		Notes:
		Like working with a raw socket, the contents don't matter, but they do have to fit within 
		system memory.
		'''

		wm = WireMsg()
		status = wm.read(self.session)
		if status.error():
			return status
		
		if wm.code != 'OgMsg' or not 'Payload' not in wm.attachments:
			return RetVal(ErrClientError)

		status = self.key.decrypt(wm.attachments['Payload'])
		if status.error():
			return status
		
		status = wm.unflatten(status['data'])
		if status.error():
			return status

		if 'Data' not in wm.attachments or 'NextKey' not in wm.attachments:
			return RetVal(ErrInvalidMsg)
		
		next_key_str = CryptoString(wm.attachments['NextKey'])
		if not next_key_str.is_valid():
			return RetVal(ErrKeyError)
		
		self.nextkey = SecretKey(next_key_str)

		return wm.attachments['Data']

	def write_data(self, data: bytes) -> RetVal:
		'''Writes raw byte data to the network connection'''

		if not data:
			return RetVal(ErrEmptyData)
		
		wm = WireMsg('EncMsg')
		wm.attachments['Data'] = data
		padding = secrets.token_bytes(secrets.randbelow(16)+1)
		wm.attachments['Padding'] = str(b85encode(padding))
		wm.attachments['NextKey'] = self.nextkey.as_string()

		status = wm.flatten()
		if status.error():
			return status
		
		status = self.key.encrypt(status['bytes'])
		if status.error():
			return status
		
		wrapper = WireMsg('OgMsg')
		wrapper.attachments['Payload'] = status['data']
		status = wrapper.write(self.session)
		if status.error():
			return status
		
		return RetVal()
