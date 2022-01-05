import socket

from retval import RetVal, ErrBadType, ErrEmptyData

from pyoganesson.field import DataField, FieldType

# Constants and Configurable Globals

# MaxCommandLength is the maximum number of bytes a command is permitted to be. Note that
# bulk transfers are not subject to this restriction -- just the initial command.
MinCommandLength = 35

MaxCommandLength = 16384

PacketSessionTimeout = 30.0

# WirePacket type codes
SinglePacket = 21

# Codes for multipart message handling
OgMultipartPacket = 22
OgMultipart = 23
OgMultipartFinal = 24


def is_packet_type_valid(ptype: int) -> bool:
	'''Returns true if the specified packet type is valid'''
	return SinglePacket <= ptype <= OgMultipartFinal


class PacketSession:
	'''PacketSession is for easily handling socket timeouts'''

	def __init__(self, conn: socket.socket, timeout=PacketSessionTimeout):
		self.conn = conn
		if conn is not None:
			conn.settimeout(timeout)

	def read_wire_packet(self) -> RetVal:
		'''A method used to read individual packet messages from a socket and to assemble 
		multipart packets into one contiguous byte array'''

		df = DataField()
		
		status = df.recv(self.conn)
		if status.error():
			return status
		
		out_type = 0
		if df.type == SinglePacket:
			return RetVal().set_value('field', df)
		if df.type in [OgMultipart, OgMultipartFinal]:
			return RetVal('ErrMultipartSession')
		if df.type == OgMultipartPacket:
			out_type = OgMultipartPacket
		else:
			return RetVal('ErrInvalidMsg')

		# We got this far, so we have a multipart message which we need to reassemble.

		# The value was already checked by the unflatten() call in recv(), so no need to worry here
		total_size = df.get()['value']
		msgparts = []
		size_read = 0
		while size_read < total_size:
			status = df.recv(self.conn)
			if status.error():
				return status
			
			msgparts.append(df.value)
			if df.type != 'bytes':
				return RetVal('ErrBadType')
			
			# The field is expected to be a byte string, so no need to call get()
			size_read = size_read + len(df.value)

			if df.type == OgMultipartFinal:
				break
		
		out = DataField()
		out.type = out_type
		out.value = b''.join(msgparts)
		if len(out.value) != total_size:
			return RetVal('ErrSize')
		
		return RetVal().set_value('field',out)

	def write_wire_packet(self, packet: DataField) -> RetVal:
		'''A method used to read individual packet messages from a socket and to assemble 
		multipart packets into one contiguous byte array'''

		if not is_packet_type_valid(packet.type):
			return RetVal(ErrBadType)
		
		if not packet.value:
			return RetVal(ErrEmptyData)

		value_size = MaxCommandLength-3

		# If the message Value is small enough to fit into a single message chunk, just send it and
		# be done.
		if len(packet.value) < value_size:
			return packet.send(self.conn)

		# If the message is bigger than the max command length, then we will send the value as
		# a multipart message. This takes more work internally, but the benefits at the application
		# level are worth it. Fortunately, by using a binary wire format, we don't have to flatten
		# the message into JSON and deal with escaping and all sorts of other complications.

		# The initial message that indicates that it is the start of a multipart message contains 
		# the total message size in the Value. All messages that follow contain the actual message 
		# data. The size Value is actually a decimal string of the total message size.

		msglen = len(packet.value)
		status = DataField('multipartpacket', msglen).send(self.conn)
		if status.error():
			return status

		index = 0
		while index + msglen:
			status = DataField('multipart', packet.value[index:index + value_size]).send(self.conn)
			if status.error():
				return status
			
			index = index + value_size
		
		return DataField('multipartfinal', packet.value[index:]).send(self.conn)
