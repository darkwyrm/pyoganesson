
class FakeSocket:
	'''FakeSocket is a stand-in for a real socket used to avoid async-await headaches'''

	def __init__(self):
		self.buffer = None
		self.flags = None

	def send(self, data: bytes, _=0) -> int:
		'''Writes the data to the fake socket'''
		if self.buffer:
			self.buffer = self.buffer + data
		else:
			self.buffer = data
		
		return len(data)

	def recv(self, bufsize=0, _=0) -> bytes:
		'''Reads data from the fake socket'''
		
		if not self.buffer:
			return None
		
		if bufsize:
			outsize = min(bufsize, len(self.buffer))
		else:
			outsize = len(self.buffer)
		
		out = self.buffer[:outsize]
		if len(self.buffer) > outsize:
			self.buffer = self.buffer[outsize:]
		else:
			self.buffer = None
		
		return out

	def settimeout(self, _: float):
		'''settimeout is a no-op for socket compatibility'''
