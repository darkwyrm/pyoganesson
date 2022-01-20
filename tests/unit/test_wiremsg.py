import inspect

from pyoganesson.field import DataField
from pyoganesson.wiremsg import WireMsg

def funcname() -> str:
	'''Returns the name of the current function'''
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_add_field():
	'''Tests WireMsg.add_field()'''

	wm = WireMsg('test')

	status = wm.add_field(None, 1)
	assert status.error(), f"{funcname()}: add_field failed to catch empty data"

	status = wm.add_field(1, 1)
	assert status.error(), f"{funcname()}: add_field failed to catch non-string index"

	status = wm.add_field('1', 100)
	assert not status.error(), f"{funcname()}: error adding field: {status.error()}"
	expected_data = {'1': DataField('int8', 100)}
	assert len(wm.attachments) == 1 and wm.attachments == expected_data, \
		f"{funcname()}: internal data mismatch for add_field('1', 100)"

	status = wm.add_field('2', 1000, 'uint8')
	assert status.error(), f"{funcname()}: add_field failed to catch out-of-range value for type"

	expected_data['2'] = DataField('uint16', 1000)
	status = wm.add_field('2', 1000, 'uint16')
	assert not status.error(), f"{funcname()}: error adding field: {status.error()}"
	assert len(wm.attachments) == 2 and wm.attachments == expected_data, \
		f"{funcname()}: internal data mismatch for add_field('2', 1000, 'uint16')"


def test_field_misc():
	'''Tests other misc WireMsg field methods'''

	wm = WireMsg('test')
	
	# setup
	status = wm.add_field('1', 100, 'uint8')
	assert not status.error(), \
		f"{funcname()}: error adding field ('1', 100, 'uint8'): {status.error()}"
	status = wm.add_field('2', 1000, 'uint16')
	assert not status.error(), \
		f"{funcname()}: error adding field ('2', 1000, 'uint16'): {status.error()}"
	status = wm.add_field('test', 'foo')
	assert not status.error(), \
		f"{funcname()}: error adding field ('test', 'foo'): {status.error()}"

	# has_field()	
	assert wm.has_field('1'), f"{funcname()}: has_field() failed to detect existing field"
	assert not wm.has_field(''), f"{funcname()}: has_field() failed to handle empty key"
	assert not wm.has_field('X'), f"{funcname()}: has_field() failed to detect nonexistent field"

	# get_string_field()
	assert wm.get_string_field('test'), \
		f"{funcname()}: get_string_field() failed to detect existing field"
	assert not wm.get_string_field('1'), \
		f"{funcname()}: get_string_field() failed to handle non-string field"
	assert not wm.get_string_field(''), \
		f"{funcname()}: get_string_field() failed to handle empty key"
	assert not wm.has_field('X'), \
		f"{funcname()}: get_string_field() failed to detect nonexistent field"


def test_wiremsg_flatten_unflatten():
	'''Tests WireMsg.flatten()'''

	wm = WireMsg('test')
	status = wm.flatten()
	assert not status.error(), f"{funcname()}: error flattening empty wire message: {status.error()}"
	flatdata = b'\x0f\x00\x04test\x0e\x00\x05\x06\x00\x02\x00\x00'
	assert status['bytes'] == flatdata, \
		f"{funcname()}: flat empty message data mismatch: {status['bytes']}"

	wm.add_field('1', 'a')
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
	test_add_field()
	test_field_misc()
	test_wiremsg_flatten_unflatten()