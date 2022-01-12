import socket

from pyeznacl import SecretKey
from retval import RetVal

class OgServer:
	'''Handles the server side of an encrypted Oganesson messaging session'''

	def __init__(self, conn: socket.socket, fingerprint: str):
		self.conn = conn
		self.key = SecretKey()
		self.nextkey = None
		self.handlers = {}
		self.fingerprint = fingerprint		

	def Setup() -> RetVal:
		'''Handles the server side of setting up an encrypted comms channel with a client'''
		
		# Once the initial TCP connection is established, the client is expected to ask for the type
		# of session encryption expected. Anything else is an error.
