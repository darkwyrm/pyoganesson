import inspect

from pyoganesson.field import DataField, check_int_range, check_uint_range

def funcname() -> str:
	'''Returns the name of the current function'''
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_check_range():
	'''Tests the integer range-checking functions'''

	try:
		check_int_range(1,0)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass

	try:
		check_int_range(1,128)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass

	try:
		check_uint_range(1,0)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass

	try:
		check_uint_range(1,128)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass
	
	signed_tests = [ (127,8), (32000,16), (70000, 32), (0xFFFFF, 64)]
	for pair in signed_tests:
		assert check_int_range(pair[0], pair[1]), \
			"{pair[1]}-bit signed range check failed: {pair[0]}"

	unsigned_tests = [ (250,8), (65000,16), (0x20000, 32), (0x200000000, 64) ]
	for pair in unsigned_tests:
		assert check_uint_range(pair[0], pair[1]), \
			"{pair[1]}-bit signed range check failed: {pair[0]}"


def test_set():
	'''Tests DataField.set()'''

	df = DataField()
	status = df.set('uint16', 1000)
	assert not status.error(), f"{funcname()}: set('uint16', 1000) error: {status.error()}"
	assert df.value == b'\x03\xe8', f"{funcname()}: set('uint16', 1000) mismatch: {df.value}"

	status = df.set('string', 'foobar')
	assert not status.error(), f"{funcname()}: set('uint16', 1000) failed"
	assert df.value == b'foobar', f"{funcname()}: set('string', 'foobar') mismatch: {df.value}"


def test_get_flat_size():
	'''Tests DataField.get_flat_size()'''

	df = DataField()
	
	type_tests = [ ('int8', 4), ('int16', 5), ('int32', 7), 
		('int64', 11), ('float32', 7), ('float64', 11) ]
	for pair in type_tests:
		df.type = pair[0]
		assert df.get_flat_size() == pair[1], \
			f"{pair[0]} flat size mismatch: {pair[1]}"
	

def test_is_valid():
	'''Tests DataField.is_valid()'''

	df = DataField()
	
	assert not df.is_valid(), f"{funcname()}: DataField(empty) is_valid() failure"
	
	status = df.set('int8', 100)
	assert not status.error(), f"{funcname()}: set('int8', 100) error: {status.error()}"
	assert df.is_valid(), f"{funcname()}: DataField('int8', 100) is_valid() failure"

	status = df.set('string', 'baz')
	assert not status.error(), f"{funcname()}: set('string', baz) error: {status.error()}"
	assert df.is_valid(), f"{funcname()}: DataField('string', baz) is_valid() failure"


if __name__ == '__main__':
	test_check_range()
	test_set()
	test_get_flat_size()
	test_is_valid()
