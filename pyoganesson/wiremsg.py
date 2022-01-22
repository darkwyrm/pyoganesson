from retval import RetVal, ErrEmptyData, ErrBadType, ErrNotFound, ErrBadData, ErrNetworkError

from pyoganesson.field import DataField, unflatten_all
from pyoganesson.packetsession import PacketSession

class WireMsg:
	'''Represents a protocol-level message'''

	def __init__(self, msgcode = ''):
		self.code = msgcode
		self.attachments = {}
	
	def add_field(self, name: str, data: any, dtype='') -> RetVal:
		'''Method for attaching data to the message

		Parameters:
		name: the name of the field to attach
		data: the data to attach as the field value

		Returns:
		error codes only
		'''
		if not name:
			return RetVal(ErrEmptyData)
		
		if not isinstance(name, str):
			return RetVal(ErrBadType, 'field indices must be strings')
		
		if data is None:
			del self.attachments[name]
		else:
			df = DataField()
			if dtype:
				status = df.set(dtype, data)
			else:
				status = df.set_from_value(data)
			if status.error():
				return status
			
			self.attachments[name] = df
		
		return RetVal()
	
	def get_field(self, name: str) -> RetVal:
		'''Returns the value of the specified attachment
		
		Parameters:
		index: the name of the attached field to obtain

		Returns:
		field 'type': the type code of value returned
		field 'value': the value of the field
		'''

		if not name or len(self.attachments) == 0:
			return RetVal(ErrEmptyData)
		
		if name not in self.attachments:
			return RetVal(ErrNotFound)
		
		return self.attachments[name].get()
	
	def has_field(self, name: str) -> bool:
		'''Returns true if the message has the specified field'''
		return name in self.attachments
	
	def get_string_field(self, name: str) -> str:
		'''Convenience method for working with string fields
		
		Parameters:
		name: the name of the attachment to obtain
		
		Returns:
		Value of the specified string field or empty string on error.'''

		if not name or not name in self.attachments:
			return ''

		status = self.attachments[name].get()
		if status.error() or status['type'] not in ['string', 'msgcode']:
			return ''

		return status['value']
	
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
		if df.type != 'bytes':
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
