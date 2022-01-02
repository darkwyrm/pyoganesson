import socket

from retval import RetVal, ErrBadType, ErrEmptyData, ErrNetworkError

from pyoganesson.field import DataField

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

	def read_wire_packet(self) -> DataField:
		'''A method used to read individual packet messages from a socket and to assemble 
		multipart packets into one contiguous byte array'''

		# TODO: Implement PacketSession.read_wire_packet()
		return None

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
			# TODO: This construct should be replaced by a write_field() function
			try:
				bytes_written = self.conn.send(packet.flatten())
			except Exception as e:
				return RetVal().wrap_exception(e)
			
			if bytes_written == 0:
				return RetVal(ErrNetworkError, 'zero bytes sent')


		# If the message is bigger than the max command length, then we will send the value as
		# a multipart message. This takes more work internally, but the benefits at the application
		# level are worth it. Fortunately, by using a binary wire format, we don't have to flatten
		# the message into JSON and deal with escaping and all sorts of other complications.

		# The initial message that indicates that it is the start of a multipart message contains 
		# the total message size in the Value. All messages that follow contain the actual message 
		# data. The size Value is actually a decimal string of the total message size.

		msglen = len(packet.value)
		# TODO: This construct should be replaced by a write_field() function
		try:
			bytes_written = self.conn.send(DataField('uint16', msglen).flatten())
		except Exception as e:
			return RetVal().wrap_exception(e)
		
		if bytes_written == 0:
			return RetVal(ErrNetworkError, 'zero bytes sent')

		# TODO: Finish implementing PacketSession.write_wire_packet()
		
		return None
