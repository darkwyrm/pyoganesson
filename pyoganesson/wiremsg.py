from retval import RetVal, ErrEmptyData, ErrBadType, ErrNotFound, ErrBadData

from pyoganesson.field import DataField, unflatten_all

class WireMsg:
	'''Represents a protocol-level message'''

	def __init__(self, msgcode = ''):
		self.code = msgcode
		self.attachments = {}
	
	def add_field(self, index: str, data: any, dtype='') -> RetVal:
		'''Method for attaching data to the message

		Parameters:
		index: the name of the field to attach
		data: the data to attach as the field value

		Returns:
		error codes only
		'''
		if not index:
			return RetVal(ErrEmptyData)
		
		if not isinstance(index, str):
			return RetVal(ErrBadType, 'field indices must be strings')
		
		if data is None:
			del self.attachments[index]
		else:
			df = DataField()
			if dtype:
				status = df.set(dtype, data)
			else:
				status = df.set_from_value(data)
			if status.error():
				return status
			
			self.attachments[index] = df
		
		return RetVal()
	
	def get_field(self, index: str) -> RetVal:
		'''Returns the value of the specified attachment
		
		Parameters:
		index: the name of the attached field to obtain

		Returns:
		field 'type': the type code of value returned
		field 'value': the value of the field
		'''

		if not index or len(self.attachments) == 0:
			return RetVal(ErrEmptyData)
		
		if index not in self.attachments:
			return RetVal(ErrNotFound)
		
		return self.attachments[index].get()
	
	def has_field(self, index: str) -> bool:
		'''Returns true if the message has the specified field'''
		return index in self.attachments
	
	def get_string_field(self, index: str) -> str:
		'''Convenience method for working with string fields
		
		Parameters:
		index: the name of the attachment to obtain
		
		Returns:
		Value of the specified string field or empty string on error.'''

		if not index or not index in self.attachments:
			return ''

		status = self.attachments[index].get()
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
		'''Deserializes the message from a byte string'''

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
