import socket

from retval import RetVal, ErrEmptyData

from pyoganesson.field import DataField, MaxCommandLength

# Constants and Configurable Globals

MinCommandLength = 35

PacketSessionTimeout = 30.0

class PacketSession:
	'''PacketSession is for easily handling socket timeouts'''

	def __init__(self, conn: socket.socket, timeout=PacketSessionTimeout):
		self.conn = conn
		if conn is not None:
			conn.settimeout(timeout)
		self.maxsize = MaxCommandLength

	def read_packet(self) -> RetVal:
		'''A method used to read individual packet messages from a socket and to assemble 
		multipart packets into one contiguous byte array
		
		Returns:
		field 'packet': a DataField object representing the wire protocol message received
		'''

		df = DataField()
		
		status = df.recv(self.conn)
		if status.error():
			return status
		
		if df.type == 'singlepacket':
			return RetVal().set_value('packet', df)
		if df.type in ['multipart', 'multipartfinal']:
			return RetVal('ErrMultipartSession')
		if df.type != 'multipartpacket':
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

			if df.type == 'multipartfinal':
				break
			
			if df.type != 'multipart':
				return RetVal('ErrBadType')
			
			# The field is expected to be a byte string, so no need to call get()
			size_read = size_read + len(df.value)
		
		flatdata = b''.join(msgparts)
		if len(flatdata) != total_size:
			return RetVal('ErrSize')
		
		out = DataField('singlepacket', flatdata)
		
		return RetVal().set_value('packet', out)

	def write_packet(self, packet: bytes) -> RetVal:
		'''A method used to read individual packet messages from a socket and to assemble 
		multipart packets into one contiguous byte array
		
		Parameters:
		packet: a wire protocol message to be sent

		Returns:
		field 'size_written': the number of bytes sent
		'''

		if not packet:
			return RetVal(ErrEmptyData)

		packet_size = self.maxsize-3

		# If the message Value is small enough to fit into a single message chunk, just send it and
		# be done.
		if len(packet) < packet_size:
			return DataField('singlepacket', packet).send(self.conn)

		# If the message is bigger than the max command length, then we will send the value as
		# a multipart message. This takes more work internally, but the benefits at the application
		# level are worth it. Fortunately, by using a binary wire format, we don't have to flatten
		# the message into JSON and deal with escaping and all sorts of other complications.

		# The initial message that indicates that it is the start of a multipart message contains 
		# the total message size in the Value. All messages that follow contain the actual message 
		# data. The size Value is actually a decimal string of the total message size.

		msglen = len(packet)
		status = DataField('multipartpacket', msglen).send(self.conn)
		if status.error():
			return status
		bytes_sent = status['size_sent']

		index = 0
		while index + packet_size < msglen:
			status = DataField('multipart', packet[index:index + packet_size]).send(self.conn)
			if status.error():
				return status
			
			bytes_sent = bytes_sent + status['size_sent']
			index = index + packet_size
		
		status = DataField('multipartfinal', packet[index:]).send(self.conn)
		if status.error():
			return status
		
		bytes_sent = bytes_sent + status['size_sent']
		return RetVal().set_value('size_sent', bytes_sent)
