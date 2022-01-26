import socket
from threading import Thread, Lock
from time import sleep

from pyoganesson.session import OgServer, OgClient

def og_session_client(mutex: Lock, port: int):
	'''Function representing the client in test_og_session() test'''

	# This forces the client to wait until the server thread is ready
	mutex.acquire()
	mutex.release()
	sleep(.1)

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('localhost',port))

	c = OgClient(sock, '123456789', 'abcdef')
	status = c.Setup()
	assert not status.error(), f"Error setting up client-side session: {status.error()}"

	status = c.write_data(b'0000000000')
	assert not status.error(), f"Client error writing data: {status.error()}"


def test_og_session():
	'''Tests Og session setup and communications'''

	testport = 3000
	mutex = Lock()
	mutex.acquire()
	t = Thread(target=og_session_client, args=(mutex, testport))
	t.start()

	listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listener.bind(('localhost', testport))

	mutex.release()
	
	listener.listen(1)
	conn, _ = listener.accept()

	server = OgServer(conn, 'abcdef')
	status = server.Setup()
	assert not status.error(), f"Error setting up server-side session: {status.error()}"

	status = server.read_data()
	assert not status.error(), f"Server error reading data: {status.error()}"
	assert status['Data'] == b'0000000000', f"Data read mismatch. Got {status['Data']}"
	

if __name__ == '__main__':
	test_og_session()
