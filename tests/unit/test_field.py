import inspect

from pyoganesson.field import DataField, check_int_range, check_uint_range, field_type_to_string

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
	status = df.set(DataField.UInt16, 1000)
	assert not status.error(), f"{funcname()}: set(UInt16, 1000) error: {status.error()}"
	assert df.value == b'\x03\xe8', f"{funcname()}: set(UInt16, 1000) mismatch: {df.value}"

	status = df.set(DataField.String, 'foobar')
	assert not status.error(), f"{funcname()}: set(UInt16, 1000) failed"
	assert df.value == b'foobar', f"{funcname()}: set(String, 'foobar') mismatch: {df.value}"


def test_get_flat_size():
	'''Tests DataField.get_flat_size()'''

	df = DataField()
	
	type_tests = [ (DataField.Int8, 4), (DataField.Int16, 5), (DataField.Int32, 7), 
		(DataField.Int64, 11), (DataField.Float32, 7), (DataField.Float64, 11) ]
	for pair in type_tests:
		df.type = pair[0]
		assert df.get_flat_size() == pair[1], \
			f"{field_type_to_string(pair[0])} flat size mismatch: {pair[1]}"
	

if __name__ == '__main__':
	test_check_range()
	test_set()
	test_get_flat_size()
