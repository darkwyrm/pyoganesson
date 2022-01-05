import asyncio
import socket

from pyoganesson.packetsession import PacketSession

async def wire_packet_listener():
	'''Function for use with test_write_wire_packet(). It listens for network connections.'''
	listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listener.bind((socket.gethostbyname(), 3000))
	await listener.listen(5)
	# TODO: finish wire_packet_listener()


async def wire_packet_writer():
	'''Function which sends the message for the write_wire_packet test'''
	# TODO: finish wire_packet_writer()


def test_write_wire_packet():
	'''Tests PacketSession write_wire_packet()'''
	asyncio.gather(wire_packet_listener(), wire_packet_writer())


if __name__ == '__main__':
	test_write_wire_packet()
