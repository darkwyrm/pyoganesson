from retval import RetVal, ErrEmptyData, ErrBadData, ErrNetworkError

from pyoganesson.field import DataField, unflatten_all
from pyoganesson.packetsession import PacketSession

ErrInvalidMsg = 'ErrInvalidMsg'

class WireMsg:
	'''Represents a protocol-level message'''

	def __init__(self, msgcode = ''):
		self.code = msgcode
		self.attachments = {}
	
	def flatten(self) -> RetVal:
		'''Serializes the message into a byte string
		
		Returns:
		field 'bytes': flattened byte string. Only returned on success.
		'''
		codefield = DataField('msgcode', self.code)
		mapfield = DataField('map', self.attachments)
		
		return RetVal().set_value('bytes', codefield.flatten() + mapfield.flatten())

	def unflatten(self, data: bytes) -> RetVal:
		'''Deserializes a byte string into the message object
		
		Parameters:
		data: a byte string containing flattened DataField data

		Returns:
		Errors only
		'''

		status = unflatten_all(data)
		if status.error():
			return status
		
		fields = status['fields']
		status = fields[0].get()
		if status.error():
			return status
		if 'type' not in status or status['type'] != 'msgcode' or 'value' not in status:
			return RetVal(ErrBadData)
		self.code = status['value']

		status = fields[1].get()
		if status.error():
			return status
		if 'type' not in status or status['type'] != 'map' or 'value' not in status:
			return RetVal(ErrBadData)
		self.attachments = status['value']

		return RetVal()

	def read(self, session: PacketSession) -> RetVal:
		'''Reads a message from a PacketSession
		
		Returns:
		Errors only
		'''

		if not session:
			return RetVal(ErrEmptyData)

		status = session.read_packet()
		if status.error():
			return status
		
		if 'packet' not in status:
			return RetVal(ErrNetworkError)
		
		df = status['packet']
		if df.type != 'singlepacket':
			return RetVal(ErrBadData)
		
		# We can skip the get() call because this data field is a byte array containing flattened
		# DataFields
		return self.unflatten(df.value)

	def write(self, session: PacketSession) -> RetVal:
		'''Sends the message over a PacketSession
		
		Returns:
		Errors only
		'''
		
		if not session or not self.code:
			return RetVal(ErrEmptyData)

		status = self.flatten()
		if status.error():
			return status
		
		return session.write_packet(status['bytes'])
