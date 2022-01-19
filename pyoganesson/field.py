import socket
import struct

from retval import RetVal, ErrBadType, ErrBadValue, ErrOutOfRange, ErrBadData, ErrNetworkError

# The DataField structure is the foundation of the lower levels of Oganesson messaging and is used
# for data serialization. The serialized format consists of a type code, a 'uint16' length, and a
# byte array of up to 64K.

_typeinfo_lookup = {}

# Lookup table to convert msg type codes to their string names
_typename_code_lookup = {
	0:'unknown',
	1:'int8',
	2:'int16',
	3:'int32',
	4:'int64',
	5:'uint8',
	6:'uint16',
	7:'uint32',
	8:'uint64',
	9:'string',
	10:'bool',
	11:'float32',
	12:'float64',
	13:'bytes',
	14:'map',
	15:'msgcode',
	21:'singlepacket',
	22:'multipartpacket',
	23:'multipart',
	24:'multipartfinal'
}

# Lookup table to convert Python variable types to type strings. Note that this table can't be
# used directly. Call get_type_from_value() because additional processing is needed beyond
# the basic lookup here
_typename_type_lookup = {
	int:'int',
	str:'string',
	bool:'bool',
	float:'float64',
	bytes:'bytes',
	dict:'map'
}

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


def unflatten_all(data: bytes) -> RetVal():
	'''Unflattens all DataFields in a byte string
	
	Parameters:
	data: a byte string containing a series of flattened DataField instances
	
	Returns:
	field 'fields': a list of DataField objects
	'''

	# Minimum size for a DataField is 4 bytes - 1 byte type code, 2 bytes size, 1 byte data
	if len(data) < 4:
		return RetVal(ErrBadData)

	out = []
	start_index = 0
	while start_index < len(data):

		try:
			fieldlen = struct.unpack('!H', data[start_index+1:start_index+3])[0]
		except:
			return RetVal(ErrBadData, f"bad value size in field {len(out)}")
		
		end_index = start_index + 2 + fieldlen + 1
		if end_index > len(data):
			return RetVal('ErrSize')
		
		df = DataField()
		status = df.unflatten(data[start_index:end_index])
		if status.error():
			return status
		out.append(df)

		start_index = end_index

	return RetVal().set_value('fields', out)


def pack_encode(value: str, _) -> bytes:
	'''Value serialization function which converts strings to binary arrays.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, str):
		raise TypeError('pack_encode() requires a string value')
	
	return value.encode()


def unpack_decode(value: str, _) -> str:
	'''Value deserialization function which converts binary arrays to strings.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, bytes):
		raise TypeError('unpack_decode() requires a binary string')

	return value.decode()


def pack_map(value: dict, _) -> bytes:
	'''Value serialization function which flattens a dictionary.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, dict):
		raise TypeError('pack_map() requires a dictionary')
	
	fields = [ ]

	# Start with a DataField item which indicates the size of the container
	fields.append(struct.pack('!B', _typeinfo_lookup['uint16'][0]) + struct.pack('!H', 2) + 
		struct.pack('!H', len(value)))

	for k,v in value.items():
		if not isinstance(k, str):
			raise TypeError('pack_map requires string keys')
		
		fields.append(DataField('string', k).flatten())

		if isinstance(v, DataField):
			if not v.is_valid():
				return None
			fields.append(v.flatten())
			continue
		
		vf = DataField()
		status = vf.set_from_value(v)
		if status.error():
			return None
		fields.append(vf.flatten())

	return b''.join(fields)


def unpack_map(value: bytes, _) -> tuple:
	'''Value deserialization function which unflattens a dictionary.
	
	To ensure compatibility with the other pack functions, it accepts a format string which is 
	summarily ignored.'''
	if not isinstance(value, bytes):
		raise TypeError('unpack_map() requires a binary string')

	# 5 bytes = an empty dictionary
	if len(value) < 5:
		return None
	
	# The first DataField in a flattened should be a uint16 containing the number of key-value pairs
	status = unflatten_all(value)
	if status.error():
		return None
	
	fields = status['fields']
	status = fields[0].get()
	if status.error() or status['type'] != 'uint16':
		return None
	itemcount = status['value']
	listlen = (itemcount*2)+1
	if len(fields) != listlen:
		return None

	out = {}
	index = 1
	while index < listlen:

		status = fields[index].get()
		if status.error() or status['type'] != 'string':
			return None
		
		key = status['value']

		status = fields[index+1].get()
		if status.error():
			return None
		
		out[key] = status['value']

		index = index + 2

	return (out,)


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


def pack_pack(value: any, packformat: str) -> bytes:
	'''Value serialization function which applies struct.pack, given a value and a format string.
	
	The format string required is the one utilized by struct.pack()'''
	return struct.pack(packformat, value)


def unpack_unpack(value: bytes, packformat: str) -> any:
	'''Value deserialization function which applies struct.unpack, given a value and a format string.
	
	The format string required is the one utilized by struct.unpack()'''
	return struct.unpack(packformat, value)


def init_type_info():
	'''Sets up all the type information needed by the DataField-related classes'''
	
	_typeinfo_lookup['unknown'] = (0, None, None, None, 0, None)
	_typeinfo_lookup['int8'] = (1, pack_pack, unpack_unpack, '!b', 1, int)
	_typeinfo_lookup['int16'] = (2, pack_pack, unpack_unpack,'!h', 2, int)
	_typeinfo_lookup['int32'] = (3, pack_pack, unpack_unpack, '!i', 4, int)
	_typeinfo_lookup['int64'] = (4, pack_pack, unpack_unpack, '!q', 8, int)
	_typeinfo_lookup['uint8'] = (5, pack_pack, unpack_unpack, '!B', 1, int)
	_typeinfo_lookup['uint16'] = (6, pack_pack, unpack_unpack, '!H', 2, int)
	_typeinfo_lookup['uint32'] = (7, pack_pack, unpack_unpack, '!I', 4, int)
	_typeinfo_lookup['uint64'] = (8, pack_pack, unpack_unpack, '!Q', 8, int)
	_typeinfo_lookup['string'] = (9, pack_encode, unpack_decode, None, 0, str)
	_typeinfo_lookup['bool'] = (10, pack_pack, unpack_unpack, '!?', 1, bool)
	_typeinfo_lookup['float32'] = (11, pack_pack, unpack_unpack, '!f', 4, float)
	_typeinfo_lookup['float64'] = (12, pack_pack, unpack_unpack, '!d', 8, float)
	_typeinfo_lookup['bytes'] = (13, pack_stub, unpack_stub, None, 0, bytes)
	
	# 'map's are just a series of DataFields. The payloads themselves are 'uint16''s
	# containing the number of items to follow that belong to the container. The actual item
	# count is half of the number of actual DataFields to follow -- a DataField map item is a 
	# string field paired with another field. 
	_typeinfo_lookup['map'] = (14, pack_map, unpack_map, '!H', 2, dict)
	
	# Message codes are strings, but they need to be different from the string type for clarity
	_typeinfo_lookup['msgcode'] = (15, pack_encode, unpack_decode, None, 0, str)

	# WirePacket type codes
	_typeinfo_lookup['singlepacket'] = (21, pack_stub, unpack_stub, None, 0, bytes)
	_typeinfo_lookup['multipartpacket'] = (22, pack_pack, unpack_unpack, '!H', 0, int)
	_typeinfo_lookup['multipart'] = (23, pack_stub, unpack_stub, None, 0, bytes)
	_typeinfo_lookup['multipartfinal'] = (24, pack_stub, unpack_stub, None, 0, bytes)


def is_valid_type(typename: str):
	'''Returns true if the string passed identifies a valid field type descriptor'''
	return typename != 'unknown' and typename in _typeinfo_lookup


def get_type_code(typename: str) -> int:
	'''Returns the integer type code for the data type or a negative number on error'''
	if is_valid_type(typename):
		return _typeinfo_lookup[typename][0]
	return -1


def get_pack_code(typename: str) -> any:
	'''Returns the struct.pack() code for the field type or None on error'''
	if is_valid_type(typename):
		return _typeinfo_lookup[typename][3]
	return None


def get_type_size(typename: str) -> int:
	'''Returns the number of bytes occupied by the data type or a negative number on error'''
	if is_valid_type(typename):
		return _typeinfo_lookup[typename][4]
	return -1


def get_type(typename: str) -> any:
	'''Returns the Python type for the field type or None on error'''
	if is_valid_type(typename):
		return _typeinfo_lookup[typename][5]
	return None


def get_type_from_code(typecode: int) -> str:
	'''Returns the name of the type indicated by the passed code or a negative number on error'''
	if typecode in _typename_code_lookup:
		return _typename_code_lookup[typecode]
	return -1


def get_type_from_value(value: any) -> str:
	'''Returns the type name based on a value provided or an empty string on error'''

	if type(value) not in _typename_type_lookup:
		return ''
	
	typestr = _typename_type_lookup[type(value)]
	if typestr != 'int':
		return typestr
	
	checktable = [
		8,
		16,
		32,
		64
	]
	for i in checktable:
		if check_int_range(value, i):
			return 'int' + str(i)
		elif check_uint_range(value, i):
			return 'uint' + str(i)
	
	return ''


def code_to_type(typecode: int) -> str:
	'''Returns the name of the type indicated by the passed code or an empty string on error'''
	if typecode in _typename_code_lookup:
		return _typename_code_lookup[typecode]
	return ''


def pack(typename: str, value: any) -> bytes:
	'''Runs the pack method for the type'''
	packer = _typeinfo_lookup[typename][1]
	if not packer:
		return None
	return packer(value, get_pack_code(typename))


def unpack(typename: str, value: any) -> bytes:
	'''Runs the unpack method for the type'''
	unpacker = _typeinfo_lookup[typename][2]
	if not unpacker:
		return None
	return unpacker(value, get_pack_code(typename))


class DataField:
	'''The DataField class manages the message type codes and associated data sizes'''

	def __init__(self, field_type = '', field_value = None):
		self.type = ''
		self.value = None
		if field_type != '' and field_value is not None:
			self.set(field_type, field_value)
	
	def __eq__(self, b):
		if not isinstance(b, DataField):
			return False
		
		return self.type == b.type and self.value == b.value

	def __ne__(self, b):
		if not isinstance(b, DataField):
			return False
		
		return self.type != b.type or self.value != b.value

	def get_flat_size(self) -> int:
		'''get_flat_size() returns the number of bytes occupied by the field when serialized.
		
		A negative value is returned if there is an error
		'''

		if not is_valid_type(self.type):
			return -1
		
		if self.type in ['bytes', 'string', 'msgcode']:
			# Strings and Byte arrays are limited to 65535 bytes. Considering these messages are
			# lightweight, that should be plenty.
			value_length = min(65535, len(self.value))
			return 3+value_length

		return get_type_size(self.type)+3

	def is_valid(self) -> bool:
		'''Returns true if the specified value is a valid DataField type code.
		
		Because the Unknown type is treated as an error condition, passing unknown to this 
		function will result in False being returned.
		'''

		# Because get_flat_size() has to have a case to handle every type of field, if we get a
		# negative value, it's because the field type is invalid.
		flat_size = self.get_flat_size()
		
		return flat_size > 0 and len(self.value) == flat_size - 3

	def set_from_value(self, field_value: any) -> RetVal():
		'''Sets the field's value to whatever is passed to the function.

		Notes:
		This version of set tries to determine the attachment type based on the value passed.
		'''
		typename = get_type_from_value(field_value)
		if not typename:
			return RetVal(ErrBadType)
		
		return self.set(typename, field_value)

	def set(self, field_type: int, field_value: any) -> RetVal():
		'''Sets the field's value to whatever is passed to the function.

		A type specifier is required because of the framework's strict typing. Objects and lists 
		are not supported. Passing a dictionary to this function will set the field as a map type
		and assigned its length to the length of the dictionary passed to it.
		'''

		self.type = field_type
		if not is_valid_type(self.type):
			return RetVal(ErrBadType)
		
		if isinstance(field_value, list) or isinstance(field_value, tuple):
			return RetVal(ErrBadValue)

		if not isinstance(field_value, get_type(self.type)):
			return RetVal(ErrBadValue)
		
		if self.type in ['string', 'msgcode', 'bytes']:
			self.value = pack(self.type, field_value[:min(65535, len(field_value))])
			return RetVal()
		
		if self.type.startswith('int'):
			if not check_int_range(field_value, get_type_size(self.type)*8):
				return RetVal(ErrOutOfRange)
		elif self.type.startswith('uint'):
			if not check_uint_range(field_value, get_type_size(self.type)*8):
				return RetVal(ErrOutOfRange)
		
		self.value = pack(self.type, field_value)
		
		return RetVal()

	def get(self) -> RetVal:
		'''Returns the value of the DataField object
		
		Returns:
		field 'type': a string containing the data's type, such as 'uint16' or 'map'
		field 'value': the actual data
		'''

		if self.get_flat_size() < 0:
			return RetVal(ErrBadType)
		
		if self.type in ['string', 'msgcode']:
			return RetVal().set_values({'type':self.type, 'value':self.value.decode()})
		
		if self.type == 'bytes':
			return RetVal().set_values({'type':self.type, 'value':self.value})
		
		try:
			out = unpack(self.type, self.value)
		except:
			return RetVal(ErrBadValue)
				
		return RetVal().set_values({'type':self.type, 'value':out[0]})

	def flatten(self) -> bytes:
		'''Returns a byte array representing the data field'''
		
		return struct.pack('!B', get_type_code(self.type)) + \
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
		
		typename = code_to_type(type_code)
		if not typename:
			return RetVal(ErrBadType)
		
		try:
			value_length = struct.unpack('!H', b[1:3])[0]
		except:
			return RetVal(ErrBadValue, 'bad value length')

		if len(b[3:]) != value_length:
			return RetVal('ErrSize', 'mismatch between size indicator and data length')

		# Make sure that the data unpacks properly before assigning values to the instance

		if unpack(typename, b[3:]) is None:
			return RetVal(ErrBadValue)

		self.type = typename
		self.value = b[3:]

		return RetVal()

	def recv(self, conn: socket.socket) -> RetVal:
		'''Reads the field from a socket
		
		Parameters:
		conn: a socket to read the data from
		
		Returns:
		field 'size_received': the number of bytes read
		'''

		if not conn:
			return RetVal(ErrNetworkError)

		try:
			flatdata = conn.recv()
		except Exception as e:
			return RetVal().wrap_exception(e)
		
		if len(flatdata) == 0:
			return RetVal(ErrNetworkError, 'zero bytes read')

		status = self.unflatten(flatdata)
		if status.error():
			return status

		return RetVal().set_value('size_received', len(flatdata))

	def send(self, conn: socket.socket) -> RetVal:
		'''Transmits the field over a socket.

		Parameters:
		conn: a valid socket

		Returns:
		field 'size_sent': the number of bytes sent over the network

		Notes:
		The caller is responsible for ensuring the flattened data will fit in the network buffer.
		'''
		
		if not conn:
			return RetVal(ErrNetworkError)

		flatdata = self.flatten()
		if not flatdata:
			return RetVal(ErrBadData)
		
		try:
			bytes_written = conn.send(flatdata)
		except Exception as e:
			return RetVal().wrap_exception(e)
		
		if bytes_written == 0:
			return RetVal(ErrNetworkError, 'zero bytes sent')

		return RetVal().set_value('size_sent', bytes_written)
