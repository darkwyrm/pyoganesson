from retval import RetVal, ErrBadType, ErrBadValue, ErrOutOfRange
import struct

# The DataField structure is the foundation of the lower levels of Oganesson messaging and is used
# for data serialization. The serialized format consists of a type code, a UInt16 length, and a
# byte array of up to 64K.

def check_int_range(value: int, bitcount: int) -> bool:
	'''Returns true if the given value fits in an integer of the specified bit size.
	
	This function raises an exception if the bit count is less than one or greater than 64.'''
	
	if bitcount < 1 or bitcount > 64:
		raise ValueError('bitcount must be 1 - 64')
	
	intmin = -(1 << (bitcount - 1))
	intmax =  (1 << (bitcount - 1)) - 1
	
	return intmin <= value <= intmax


def check_uint_range(value: int, bitcount: int) -> bool:
	'''Returns true if the given value fits in an unsigned integer of the specified bit size.
	
	This function raises an exception if the bit count is less than one or greater than 64.'''
	
	if bitcount < 1 or bitcount > 64:
		raise ValueError('bitcount must be 1 - 64')
	
	return 0 <= value <= (1 << bitcount) - 1


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

	def __init__(self, field_type = 0, field_value = None):
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

	def set(self, field_type: int, field_value: any) -> RetVal():
		'''Sets the field's value to whatever is passed to the function.

		A type specifier is required because of the framework's strict typing. Objects and lists 
		are not supported. Passing a dictionary to this function will set the field as a map type
		and assigned its length to the length of the dictionary passed to it.
		'''

		self.type = field_type
		if self.get_flat_size() < 0:
			return RetVal(ErrBadType)
		
		if isinstance(field_value, list):
			return RetVal(ErrBadValue)

		if self.type in [DataField.String, DataField.MsgCode]:
			if not isinstance(field_value, str):
				return RetVal(ErrBadValue)
			self.value = field_value[:min(65535, len(field_value))]
		
		if self.type == DataField.Byte:
			if not isinstance(field_value, bytes):
				return RetVal(ErrBadValue)
			self.value = field_value[:min(65535, len(field_value))]

		if self.type == DataField.Int8:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_int_range(field_value, 8):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!b', field_value)

		if self.type == DataField.UInt8:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_uint_range(field_value, 8):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!B', field_value)

		if self.type == DataField.Int16:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_int_range(field_value, 16):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!h', field_value)

		if self.type == DataField.UInt16:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_uint_range(field_value, 16):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!H', field_value)

		if self.type == DataField.Int32:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_int_range(field_value, 32):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!i', field_value)

		if self.type == DataField.UInt32:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_uint_range(field_value, 32):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!I', field_value)

		if self.type == DataField.Int64:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_int_range(field_value, 64):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!q', field_value)

		if self.type == DataField.UInt64:
			if not isinstance(field_value, int):
				return RetVal(ErrBadValue)
			
			if not check_uint_range(field_value, 64):
				return RetVal(ErrOutOfRange)
			
			self.value = struct.pack('!Q', field_value)

		if self.type == DataField.Bool:
			if not isinstance(field_value, bool):
				return RetVal(ErrBadValue)
			
			self.value = struct.pack('!?', field_value)

		if self.type == DataField.Float32:
			if not isinstance(field_value, float):
				return RetVal(ErrBadValue)
			
			self.value = struct.pack('!f', field_value)

		if self.type == DataField.Float64:
			if not isinstance(field_value, double):
				return RetVal(ErrBadValue)
			
			self.value = struct.pack('!d', field_value)

		if self.type == DataField.Map:
			if not isinstance(field_value, dict):
				return RetVal(ErrBadValue)
			
			self.value = struct.pack('!H', field_value)

		return RetVal()