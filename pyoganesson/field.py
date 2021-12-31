from retval import RetVal, ErrBadType

# The DataField structure is the foundation of the lower levels of Oganesson messaging and is used
# for data serialization. The serialized format consists of a type code, a uint16 length, and a
# byte array of up to 64K.

DFUnknownType = 0
DFInt8Type = 1
DFInt16Type = 2
DFInt32Type = 3
DFInt64Type = 4
DFUInt8Type = 5
DFUInt16Type = 6
DFUInt32Type = 7
DFUInt64Type = 8
DFStringType = 9
DFBoolType = 10
DFFloat32Type = 11
DFFloat64Type = 12
DFByteType = 13

def get_type_size(t: int) -> int:
	'''get_type_size() returns the number of bytes occupied by the specified field type.

	For fields which have a variable size, such as byte arrays or strings, 0 is returned. -1 is 
	returned for invalid types.
	'''

	if t in [DFInt8Type, DFUInt8Type, DFBoolType]:
		return 1
	if t in [DFInt16Type, DFUInt16Type]:
		return 2
	if t in [DFInt32Type, DFUInt32Type]:
		return 4
	if t in [DFInt64Type, DFUInt64Type]:
		return 8
	
	return -1

def is_valid_field_type(t: int) -> bool:
	'''Returns true if the specified value is a valid DataField type code.
	
	Because the Unknown type is treated as an error condition, passing DFUnknownType to this 
	function will result in False being returned.
	'''

	return t > DFUnknownType and t <= DFByteType


# Maps are just a series of DataFields. The payloads themselves are uint16's
# containing the number of items to follow that belong to the container. For maps, the item
# count is half of the number of actual DataFields to follow -- a DataField map consists of
# a list of pairs of a DFStringType and another field. For complexity reasons maps and lists
# may not be nested.
DFMapType = 14

# Message codes are strings, but they need to be different from the string type for clarity
DFMsgCodeType = 15

class DataField:
	'''DataField is the foundation for the Oganesson wire message data serialization format'''
	
	def __init__(self):
		self.type = 0
		self.value = list()

	def set(self, type_code: int, v: any) -> RetVal:
		
		# TODO: implement DataField.set()
		
		return RetVal()