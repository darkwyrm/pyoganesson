import inspect

from pyoganesson.field import DataField
from pyoganesson.wiremsg import WireMsg

def funcname() -> str:
	'''Returns the name of the current function'''
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_wiremsg_flatten_unflatten():
	'''Tests WireMsg.flatten()'''

	wm = WireMsg('test')
	status = wm.flatten()
	assert not status.error(), f"{funcname()}: error flattening empty wire message: {status.error()}"
	flatdata = b'\x0f\x00\x04test\x0e\x00\x05\x06\x00\x02\x00\x00'
	assert status['bytes'] == flatdata, \
		f"{funcname()}: flat empty message data mismatch: {status['bytes']}"

	wm.attachments['1'] = 'a'
	status = wm.flatten()
	assert not status.error(), \
		f"{funcname()}: error flattening wire message with data: {status.error()}"
	flatdata = b'\x0f\x00\x04test\x0e\x00\r\x06\x00\x02\x00\x01\t\x00\x011\t\x00\x01a'
	assert status['bytes'] == flatdata, \
		f"{funcname()}: flat populated message data mismatch.\n" + \
			f"Want:  {flatdata}\nGot: {status['bytes']}"

	wm = WireMsg()
	flatdata = b'\x0f\x00\x04test\x0e\x00\x05\x06\x00\x02\x00\x00'
	status = wm.unflatten(flatdata)
	assert not status.error(), f"{funcname()}: error unflattening empty wire message: {status.error()}"
	assert wm.code == 'test' and len(wm.attachments) == 0, \
		f"{funcname()}: unflattened empty message data mismatch"

	wm = WireMsg()
	flatdata = b'\x0f\x00\x04test\x0e\x00\r\x06\x00\x02\x00\x01\t\x00\x011\t\x00\x01a'
	status = wm.unflatten(flatdata)
	assert not status.error(), \
		f"{funcname()}: error unflattening wire message with data: {status.error()}"
	assert wm.code == 'test' and len(wm.attachments) == 1 and '1' in wm.attachments and \
		wm.attachments['1'] == 'a', f"{funcname()}: unflattened empty message data mismatch"


if __name__ == '__main__':
	test_wiremsg_flatten_unflatten()
