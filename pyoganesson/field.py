import socket
import struct

from retval import RetVal, ErrBadType, ErrBadValue, ErrOutOfRange, ErrBadData, ErrNetworkError

# The DataField structure is the foundation of the lower levels of Oganesson messaging and is used
# for data serialization. The serialized format consists of a type code, a 'uint16' length, and a
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


def pack_encode(value: str, _) -> bytes:
	'''Value serialization function which converts strings to binary arrays.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, str):
		raise TypeError('pack_encode() requires a string value')
	
	return value.encode()


def unpack_decode(value: str, _) -> bytes:
	'''Value deserialization function which converts binary arrays to strings.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, bytes):
		raise TypeError('unpack_decode() requires a binary string')

	return value.decode()


def pack_length(value: any, _) -> bytes:
	'''Value serialization function which flattens the value to its length.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, map) and not isinstance(value, list) and not isinstance(value, tuple):
		raise TypeError('pack_length() requires a container')
	
	return struct.pack('!H', len(value))


def unpack_length(value: any, _) -> bytes:
	'''Value deserialization function which unflattens value created by pack_length.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, bytes):
		raise TypeError('unpack_length() requires a binary string')
	
	return struct.unpack('!H', value)


def pack_stub(value: bytes, _) -> bytes:
	'''Value serialization function which returns what it is given, intended for binary arrays.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, bytes):
		raise TypeError('pack_stub() requires a byte array')
	
	return value


def unpack_stub(value: bytes, _) -> bytes:
	'''Value deserialization function which returns what it is given, intended for binary arrays.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, bytes):
		raise TypeError('unpack_stub() requires a byte array')
	
	return value


def pack_pack(value: any, format: str) -> bytes:
	'''Value serialization function which applies struct.pack, given a value and a format string.
	
	The format string required is the one utilized by struct.pack()'''
	return struct.pack(format, value)


def unpack_unpack(value: any, format: str) -> bytes:
	'''Value deserialization function which applies struct.unpack, given a value and a format string.
	
	The format string required is the one utilized by struct.unpack()'''
	return struct.unpack(format, value)


# TODO: place packer/unpacker function pairs into some constants

class FieldTypeInfo:
	'''FieldTypeInfo is just a structure to house information about a specific FieldType type'''
	
	def __init__(self, index: int, name: str, pack_string: str, bytesize: int, type_class: any):
		self.index = index
		self.name = name
		self.size = bytesize
		self.packstr = pack_string
		self.type = type_class


# TODO: Retool FieldType to remove the replace the name parameter with packer/unpacker pairs
class FieldType:
	'''The FieldType class is for handling the different types of DataField data'''
	_typeinfo_lookup = {
		'unknown' : FieldTypeInfo(0, 'unknown', None, 0, None),
		'int8' : FieldTypeInfo(1, 'int8', '!b', 1, int),
		'int16' : FieldTypeInfo(2, 'int16','!h', 2, int),
		'int32' : FieldTypeInfo(3, 'int32', '!i', 4, int),
		'int64' : FieldTypeInfo(4, 'int64', '!q', 8, int),
		'uint8' : FieldTypeInfo(5, 'uint8', '!B', 1, int),
		'uint16' : FieldTypeInfo(6, 'uint16', '!H', 2, int),
		'uint32' : FieldTypeInfo(7, 'uint32', '!I', 4, int),
		'uint64' : FieldTypeInfo(8, 'uint64', '!Q', 8, int),
		'string' : FieldTypeInfo(9, 'string', None, 0, str),
		'bool' : FieldTypeInfo(10, 'bool', '!?', 1, bool),
		'float32' : FieldTypeInfo(11, 'float32', '!f', 4, int),
		'float64' : FieldTypeInfo(12, 'float64', '!d', 8, int),
		'bytes' : FieldTypeInfo(13, 'bytes', None, 0, bytes),
		
		# 'map's are just a series of DataFields. The payloads themselves are 'uint16''s
		# containing the number of items to follow that belong to the container. The actual item
		# count is half of the number of actual DataFields to follow -- a DataField map item is a 
		# string field paired with another field. 
		'map' : FieldTypeInfo(14, 'map', '!H', 2, dict),
		
		# Message codes are strings, but they need to be different from the string type for clarity
		'msgcode' : FieldTypeInfo(15, 'msgcode', None, 0, str),

		# TODO: Add OgMessage type code info

		# WirePacket type codes
		# 'singlepacket' : FieldTypeInfo(21, 'singlepacket', , bytesize, type_class)
	}

	# Lookup table to convert msg type codes to their string names
	_typename_lookup = [
		'unknown',
		'int8',
		'int16',
		'int32',
		'int64',
		'uint8',
		'uint16',
		'uint32',
		'uint64',
		'string',
		'bool',
		'float32',
		'float64',
		'bytes',
		'map',
		'msgcode'
	]

	def __init__(self, field_type = 'unknown'):
		self.value = 'unknown'
		if field_type != 'unknown' and field_type in FieldType._typeinfo_lookup:
			self.value = field_type
	
	def is_valid_type(self):
		'''Returns true if the string passed identifies a valid field type descriptor'''
		return self.value != 'unknown' and self.value in FieldType._typeinfo_lookup
	
	def get_pack_code(self) -> any:
		'''Returns the struct.pack() code for the field type or None on error'''
		if self.is_valid_type():
			return FieldType._typeinfo_lookup[self.value].packstr
		return None
	
	def get_type(self) -> any:
		'''Returns the Python type for the field type or None on error'''
		if self.is_valid_type():
			return FieldType._typeinfo_lookup[self.value].type
		return None
	
	def get_type_code(self) -> int:
		'''Returns the number of bytes occupied by the data type or a negative number on error'''
		if self.is_valid_type():
			return FieldType._typeinfo_lookup[self.value].index
		return -1
	
	def get_type_size(self) -> int:
		'''Returns the number of bytes occupied by the data type or a negative number on error'''
		if self.is_valid_type():
			return FieldType._typeinfo_lookup[self.value].size
		return -1
	
	def get_type_from_code(self, typecode: int) -> str:
		'''Returns the name of the type indicated by the passed code or a negative number on error'''
		if 0 < typecode < len(FieldType._typename_lookup):
			return FieldType._typename_lookup[typecode]
		return -1
	
	def set_from_code(self, typecode: int) -> bool:
		'''Returns the name of the type indicated by the passed code or a negative number on error'''
		if 0 < typecode < len(FieldType._typename_lookup):
			self.value = FieldType._typename_lookup[typecode]
			return True
		return False


class DataField:
	'''The DataField class manages the message type codes and associated data sizes'''

	def __init__(self, field_type = '', field_value = None):
		self.type = ''
		self.value = None
		if field_type != '' and field_value is not None:
			self.set(field_type, field_value)
	
	def get_flat_size(self) -> int:
		'''get_flat_size() returns the number of bytes occupied by the field when serialized.
		
		A negative value is returned if there is an error
		'''

		ft = FieldType(self.type)
		if not ft.is_valid_type():
			return -1
		
		if self.type in ['bytes', 'string', 'msgcode']:
			# Strings and Byte arrays are limited to 65535 bytes. Considering these messages are
			# lightweight, that should be plenty.
			value_length = min(65535, len(self.value))
			return 3+value_length

		return ft.get_type_size()+3

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

		if self.type in ['string', 'msgcode']:
			if not isinstance(field_value, str):
				return RetVal(ErrBadValue)
			self.value = field_value[:min(65535, len(field_value))].encode()
			return RetVal()
		
		if self.type == 'bytes':
			if not isinstance(field_value, bytes):
				return RetVal(ErrBadValue)
			self.value = field_value[:min(65535, len(field_value))]
			return RetVal()
		
		ft = FieldType(self.type)
		
		if self.type == 'map':
			if not isinstance(field_value, dict):
				return RetVal(ErrBadValue)
			self.value = struct.pack(ft.get_pack_code(), len(field_value))
			return RetVal()
		
		if not isinstance(field_value, ft.get_type()):
			return RetVal(ErrBadValue)
		
		if self.type.startswith('int'):
			if not check_int_range(field_value, ft.get_type_size()*8):
				return RetVal(ErrOutOfRange)
		elif self.type.startswith('uint'):
			if not check_uint_range(field_value, ft.get_type_size()*8):
				return RetVal(ErrOutOfRange)
		
		self.value = struct.pack(ft.get_pack_code(), field_value)
		
		return RetVal()

	def get(self) -> RetVal:
		'''Returns the value of the DataField object'''

		if self.get_flat_size() < 0:
			return RetVal(ErrBadType)
		
		if self.type in ['string', 'msgcode']:
			return RetVal().set_values({'type':self.type, 'value':self.value.decode()})
		
		if self.type == 'bytes':
			return RetVal().set_values({'type':self.type, 'value':self.value})
		
		ft = FieldType(self.type)
		try:
			out = struct.unpack(ft.get_pack_code(), self.value)
		except:
			return RetVal(ErrBadValue)
				
		return RetVal().set_values({'type':self.type, 'value':out[0]})

	def flatten(self) -> bytes:
		'''Returns a byte array representing the data field'''
		
		return struct.pack('!B', FieldType(self.type).get_type_code()) + \
			struct.pack('!H', len(self.value)) + self.value

	def unflatten(self, b: bytes) -> RetVal:
		'''Sets the value of the field from the given byte array'''

		if len(b) < 4:
			return RetVal(ErrBadData, 'byte array too short')
		
		try:
			# It's really strange IMO, but b[0] is an int, but b[1:3] is a byte string. *shrug*
			type_code = struct.unpack('!B', b[0].to_bytes(1, 'big'))[0]
		except:
			return RetVal(ErrBadType)
		
		ft = FieldType()
		if not ft.set_from_code(type_code):
			return RetVal(ErrBadType)
		
		try:
			value_length = struct.unpack('!H', b[1:3])[0]
		except:
			return RetVal(ErrBadValue, 'bad value length')

		if len(b[3:]) != value_length:
			return RetVal('ErrSize', 'mismatch between size indicator and data length')

		# Make sure that the data unpacks properly before assigning values to the instance

		if ft.value in ['string', 'msgcode']:
			try:
				b[3:].decode()
			except:
				return RetVal(ErrBadValue)
		else:
			# This check is needed to handle byte array fields
			if ft.get_pack_code():
				try:
					struct.unpack(ft.get_pack_code(), b[3:])
				except:
					return RetVal(ErrBadValue)

		self.type = ft.value
		self.value = b[3:]

		return RetVal()

	def send(self, conn: socket.socket) -> RetVal:
		'''Transmits the field over a socket.

		The caller is responsible for ensuring the flattened data will fit in the network buffer.
		'''
		
		if not conn:
			return RetVal(ErrNetworkError)

		flatdata = self.flatten()
		if not flatdata:
			return RetVal(ErrBadData)
		
		try:
			bytes_written = conn.send()
		except Exception as e:
			return RetVal().wrap_exception(e)
		
		if bytes_written == 0:
			return RetVal(ErrNetworkError, 'zero bytes sent')

		return RetVal().set_value('size_sent', bytes_written)
