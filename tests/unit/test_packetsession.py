import inspect

from fakesocket import FakeSocket

from pyoganesson.field import DataField
from pyoganesson.packetsession import PacketSession


def funcname() -> str:
	'''Returns the name of the current function'''
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_write_wire_packet():
	'''Tests basic write_wire_packet() functionality'''
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
	'''Tests PacketSession write_wire_packet()'''
	sock = FakeSocket()	

	sender = PacketSession(sock)
	msg = DataField('singlepacket',b'{"Type":"TEST","Command":"ThisIsATestMessage",' \
		b'"Args": {"TestArg": "AAAAAAAAAABBBBBBBBBBCCCCCCCCCCDDDDDDDDDDEEEEEEEEEEFFFFFFFFFF' \
		b'GGGGGGGGGGHHHHHHHHHHIIIIIIIIIIJJJJJJJJJJKKKKKKKKKKLLLLLLLLLLMMMMMMMMMMNNNNNNNNNN' \
		b'OOOOOOOOOOPPPPPPPPPPQQQQQQQQQQRRRRRRRRRRSSSSSSSSSSTTTTTTTTTTUUUUUUUUUUVVVVVVVVVV' \
		b'WWWWWWWWWWXXXXXXXXXXYYYYYYYYYYZZZZZZZZZZAAAAAAAAAABBBBBBBBBBCCCCCCCCCCDDDDDDDDDD' \
		b'EEEEEEEEEEFFFFFFFFFFGGGGGGGGGGHHHHHHHHHHIIIIIIIIIIJJJJJJJJJJKKKKKKKKKKLLLLLLLLLL' \
		b'MMMMMMMMMMNNNNNNNNNNOOOOOOOOOOPPPPPPPPPPQQQQQQQQQQRRRRRRRRRRSSSSSSSSSSTTTTTTTTTT' \
		b'UUUUUUUUUUVVVVVVVVVVWWWWWWWWWWXXXXXXXXXXYYYYYYYYYYZZZZZZZZZZ12345678901234567890"}}')
	status = sender.write_wire_packet(msg)
	assert not status.error(), f'{funcname()}: error sending multipart msg: {status.error()}'

	receiver = PacketSession(sock)
	status = receiver.read_wire_packet()
	assert not status.error(), f"{funcname()}: failed to read multipart message: {status.error()}"


if __name__ == '__main__':
	test_write_wire_packet()
	test_write_multipart_wire_packet()
