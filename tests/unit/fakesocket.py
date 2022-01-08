
class FakeSocket:
	'''FakeSocket is a stand-in for a real socket used to avoid async-await headaches'''

	def __init__(self):
		self.buffer = []
		self.flags = None

	def send(self, data: bytes) -> int:
		'''Writes the data to the fake socket'''
		self.buffer.append(data)
		
		return len(data)

	def recv(self) -> bytes:
		'''Reads data from the fake socket'''
		
		if not self.buffer:
			return None
		
		return self.buffer.pop(0)

	def settimeout(self, _: float):
		'''settimeout is a no-op for socket compatibility'''
