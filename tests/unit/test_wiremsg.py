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

	# add_field()
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


def test_wiremsg_flatten():
	'''Tests WireMsg.flatten()'''

	wm = WireMsg('test')
	status = wm.flatten()
	assert not status.error(), f"{funcname()}: error flattening empty wire message: {status.error()}"
	flatdata = b'\x0f\x00\x04test\x0e\x00\x05\x06\x00\x02\x00\x00'
	assert status['bytes'] == flatdata, \
		f"{funcname()}: flat data mismatch: {status['bytes']}"

	# TODO: Finish test_wiremsg_flatten()


if __name__ == '__main__':
	test_add_field()
	test_wiremsg_flatten()