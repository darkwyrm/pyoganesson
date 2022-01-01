from retval import RetVal, ErrBadType

# The DataField structure is the foundation of the lower levels of Oganesson messaging and is used
# for data serialization. The serialized format consists of a type code, a UInt16 length, and a
# byte array of up to 64K.

class DataField:
	'''The DataField class manages the message type codes and associated data sizes'''
	Unknown = 0
	Int8 = 1
	Int16 = 2
	Int32 = 3
	Int64 = 4
	UInt8 = 5
	UInt16 = 6
	UInt32 = 7
	UInt64 = 8
	String = 9
	Bool = 10
	Float32 = 11
	Float64 = 12
	Byte = 13
	
	# Maps are just a series of DataFields. The payloads themselves are UInt16's
	# containing the number of items to follow that belong to the container. The actual item
	# count is half of the number of actual DataFields to follow -- a DataField map item is a 
	# string field paired with another field. 
	Map = 14

	# Message codes are strings, but they need to be different from the string type for clarity
	MsgCode = 15

	def __init__(self, field_type = DataField.Unknown, field_value = None):
		self.type = field_type
		self.value = field_value
	
	def get_flat_size(self) -> int:
		'''get_flat_size() returns the number of bytes occupied by the field when serialized.
		
		A negative value is returned if there is an error
		'''

		if self.type in [DataField.Byte, DataField.String, DataField.MsgCode]:
			# Strings and Byte arrays are limited to 65535 bytes. Considering these messages are
			# lightweight, that should be plenty.
			value_length = min(65535, len(self.value))
			return 3+len(value_length)
		
		if self.type in [DataField.Int8, DataField.UInt8, DataField.Bool]:
			return 1+3
		
		if self.type in [DataField.Int16, DataField.UInt16, DataField.Map]:
			return 2+3
		
		if self.type in [DataField.Int32, DataField.UInt32, DataField.Float32]:
			return 4+3
		
		if self.type in [DataField.Int64, DataField.UInt64, DataField.Float64]:
			return 8+3
		
		return -1

	def is_valid(self) -> bool:
		'''Returns true if the specified value is a valid DataField type code.
		
		Because the Unknown type is treated as an error condition, passing unknown to this 
		function will result in False being returned.
		'''

		# Because get_flat_size() has to have a case to handle every type of field, if we get a
		# negative value, it's because the field type is invalid.
		flat_size = self.get_flat_size()
		
		return flat_size > 0 and len(self.value) == flat_size - 3

