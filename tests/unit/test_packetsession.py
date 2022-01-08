import inspect

from fakesocket import FakeSocket

from pyoganesson.field import DataField
from pyoganesson.packetsession import PacketSession


def funcname() -> str:
	'''Returns the name of the current function'''
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_read_write_wire_packet():
	'''Tests basic wire packete reading and writing functionality'''
	sock = FakeSocket()	

	sender = PacketSession(sock)
	msg = DataField('singlepacket',b'foobar')
	status = sender.write_wire_packet(msg)
	assert not status.error(), f'{funcname()}: error sending msg: {status.error()}'

	receiver = PacketSession(sock)
	status = receiver.read_wire_packet()
	assert not status.error(), f"{funcname()}: failed to read message: {status.error()}"
 
	assert 'field' in status, f"{funcname()}: return message missing 'field'"
	rmsg = status['field']
	assert rmsg.type == 'singlepacket' and rmsg.value == b'foobar', \
		f"{funcname()}: return message type/value mismatch"


def test_write_multipart_wire_packet():
	'''Tests sending multipart messages with PacketSession's write_wire_packet()'''
	
	sock = FakeSocket()	

	# Normally changing the session's max packet size is not recommended, but in this case it's 
	# necessary to make the test data manageable.
	sender = PacketSession(sock)
	sender.maxsize = 10
	msg = DataField('singlepacket',b'ABCDEFGHIJKLMNOPQRS')
	status = sender.write_wire_packet(msg)
	assert not status.error(), f'{funcname()}: error sending multipart msg: {status.error()}'

	# Because the maximum buffer size is only 10 bytes, there should be room for only 7 letters per
	# message because of the 3-byte overhead for message headers.

	# The first message should contain the total size of the data
	firstmsg = b'\x16\x00\x02\x00\x13'
	assert sock.buffer[0] == firstmsg, \
		f"{funcname()}: first message data mismatch: {sock.buffer[0]}"
	
	secondmsg = b'\x17\x00\x07ABCDEFG'
	assert sock.buffer[1] == secondmsg, \
		f"{funcname()}: second message data mismatch: {sock.buffer[1]}"

	thirdmsg = b'\x17\x00\x07HIJKLMN'
	assert sock.buffer[2] == thirdmsg, \
		f"{funcname()}: third message data mismatch: {sock.buffer[2]}"

	finalmsg = b'\x18\x00\x05OPQRS'
	assert sock.buffer[3] == finalmsg, \
		f"{funcname()}: final message data mismatch: {sock.buffer[3]}"


def test_read_multipart_wire_packet():
	'''Tests receiving multipart messages with PacketSession's read_wire_packet()'''
	
	sock = FakeSocket()	

	# Normally changing the session's max packet size is not recommended, but in this case it's 
	# necessary to make the test data manageable.
	sender = PacketSession(sock)
	sender.maxsize = 10
	msg = DataField('singlepacket', b'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
	status = sender.write_wire_packet(msg)
	assert not status.error(), f'{funcname()}: error sending multipart msg: {status.error()}'

	receiver = PacketSession(sock)
	status = receiver.read_wire_packet()
	assert not status.error(), \
		f"{funcname()}: error receiving multipart message: {status.error()}"
	assert 'field' in status, \
		f"{funcname()}: field 'field' not in message"
	
	df = status['field']
	assert df.type == 'singlepacket' and df.value == b'ABCDEFGHIJKLMNOPQRSTUVWXYZ', \
		f"{funcname()}: multipart message type/value mismatch: {df.type}/{df.value}"


if __name__ == '__main__':
	test_read_write_wire_packet()
	test_write_multipart_wire_packet()
	test_read_multipart_wire_packet()
