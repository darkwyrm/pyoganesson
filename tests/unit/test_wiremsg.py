import inspect

from pyoganesson.wiremsg import WireMsg

def funcname() -> str:
	'''Returns the name of the current function'''
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_wiremsg_flatten():
	'''Tests WireMsg.flatten()'''

	wm = WireMsg('test')
	status = wm.flatten()
	assert not status.error(), f"{funcname()}: error flattening empty wire message: {status.error()}"
	flatdata = b'\x0f\x00\x04test\x0e\x00\x05\x06\x00\x02\x00\x00'
	assert status['bytes'] == flatdata, \
		f"{funcname()}: flat data mismatch: {status['bytes']}"


if __name__ == '__main__':
	test_wiremsg_flatten()
