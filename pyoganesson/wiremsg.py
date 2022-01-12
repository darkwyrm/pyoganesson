from retval import RetVal, ErrEmptyData, ErrBadType

from field import DataField 

class WireMsg:
	'''Represents a protocol-level message'''

	def __init__(self, msgcode = ''):
		self.code = msgcode
		self.attachments = {}
	
	def add_field(self, index: str, data: any) -> RetVal:
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
		
		if data == None:
			del self.attachments[index]
		else:
			df = DataField()
			status = df.set_from_value(data)
			if status.error():
				return status
			
			self.attachments[index] = df
		
		return RetVal()
	
		