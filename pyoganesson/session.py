import socket

from pyeznacl import SecretKey
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
