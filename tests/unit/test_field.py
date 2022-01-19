import inspect

from pyoganesson.field import DataField, check_int_range, check_uint_range, unflatten_all

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

	status = df.set('map', {'1':'a','2':'b'})
	assert not status.error(), f"{funcname()}: set('map', {{'1':'a','2':'b'}}) failed"
	assert df.value == b'\x06\x00\x02\x00\x02\t\x00\x011\t\x00\x01a\t\x00\x012\t\x00\x01b', \
		f"{funcname()}: set('map', {{'1':'a','2':'b'}}) mismatch: {df.value}"


def test_get():
	'''Tests DataField.get()'''

	df = DataField()

	status = df.get()
	assert status.error(), f"{funcname()}: get() failed to return an error"
	
	df.type = 'string'
	df.value = b'foobar'
	status = df.get()
	assert 'type' in status and status['type'] == 'string', \
		f"{funcname()}: get('string','foobar') type failure"
	assert 'value' in status and status['value'] == 'foobar', \
		f"{funcname()}: get('string','foobar') value failure"

	df.type = 'bytes'
	df.value = b'spam'
	status = df.get()
	assert 'type' in status and status['type'] == 'bytes', \
		f"{funcname()}: get('bytes','spam') type failure"
	assert 'value' in status and status['value'] == b'spam', \
		f"{funcname()}: get('bytes','spam') value failure"

	df.type = 'int8'
	df.value = b'\x0a'
	status = df.get()
	assert 'type' in status and status['type'] == 'int8', \
		f"{funcname()}: get('int8',10) type failure"
	assert 'value' in status and status['value'] == 10, \
		f"{funcname()}: get('int8',10) value failure"


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


def test_unflatten_all():
	'''Tests the standalone function unflatten_all()'''

	status = unflatten_all(
		b'\x06\x00\x02\x00\x02\t\x00\x011\t\x00\x01a\t\x00\x012\t\x00\x01b')
	assert not status.error(), f"{funcname()}: unflatten_all() error: {status.error()}"
	fields = status['fields']
	assert len(fields) == 5, f"{funcname()}: unflatten_all() only returned {len(fields)} fields"


def test_flatten_unflatten():
	'''Tests DataField.flatten()/unflatten()'''

	df = DataField()
	status = df.set('uint16', 1000)
	assert not status.error(), f"{funcname()}: set('uint16', 1000) error: {status.error()}"
	flattened = df.flatten()
	assert flattened == b'\x06\x00\x02\x03\xe8', \
		f"{funcname()}: flatten('uint16', 1000) mismatch: {flattened}"
	
	status = df.set('string', 'foobar')
	assert not status.error(), f"{funcname()}: set('string', foobar) error: {status.error()}"
	flattened = df.flatten()
	assert flattened == b'\x09\x00\x06foobar', \
		f"{funcname()}: flatten('string', 'foobar') mismatch: {flattened}"

	status = df.set('bytes', b'spam')
	assert not status.error(), f"{funcname()}: set('bytes', b'spam') error: {status.error()}"
	flattened = df.flatten()
	assert flattened == b'\x0d\x00\x04spam', \
		f"{funcname()}: flatten('bytes', b'spam') mismatch: {flattened}"

	status = df.set('map', {'1':'a','2':'b'})
	assert not status.error(), \
		f"{funcname()}: set('map', {{'1':'a','2':'b'}}) error: {status.error()}"
	flattened = df.flatten()
	flatmap = b'\x0e\x00\x15\x06\x00\x02\x00\x02\t\x00\x011\t\x00\x01a\t\x00\x012\t\x00\x01b'
	assert flattened == flatmap, \
		f"{funcname()}: flatten('map', {{'1':'a','2':'b'}}) mismatch: {flattened}"

	# For WireMsg to work correctly, it must be possible to flatten an empty map
	status = df.set('map', {})
	assert not status.error(), \
		f"{funcname()}: set('map', {{}}) error: {status.error()}"
	flattened = df.flatten()
	emptymap = b'\x0e\x00\x05\x06\x00\x02\x00\x00'
	assert flattened == emptymap, \
		f"{funcname()}: flatten('map', {{}}) mismatch: {flattened}"

	df.type = 'unknown'
	df.value = None
	status = df.unflatten(flatmap)
	assert not status.error(), \
		f"{funcname()}: error unflattening({flatmap}): {status.error()}"
	assert df.type == 'map', f"{funcname()}: unflatten(map) type mismatch: {df.value}"
	status = df.get()
	assert not status.error(), \
		f"{funcname()}: error getting value from unflattened map: {status.error()}"
	assert 'type' in status and status['type'] == 'map', \
		f"{funcname()}: type field missing in unflattened map get()"
	assert 'value' in status and status['value'] == {'1':'a','2':'b'}, \
		f"{funcname()}: type field value mismatch in unflattened map get(): {status['value']}"

	df.type = 'unknown'
	df.value = None
	status = df.unflatten(emptymap)
	assert not status.error(), \
		f"{funcname()}: error unflattening({emptymap}): {status.error()}"
	assert df.type == 'map', f"{funcname()}: unflatten(map) type mismatch: {df.value}"
	status = df.get()
	assert not status.error(), \
		f"{funcname()}: error getting value from unflattened map: {status.error()}"
	assert 'type' in status and status['type'] == 'map', \
		f"{funcname()}: type field missing in unflattened map get()"
	assert 'value' in status and status['value'] == {}, \
		f"{funcname()}: type field value mismatch in unflattened map get(): {status['value']}"

	df.type = 'unknown'
	df.value = None
	status = df.unflatten(b'\x09\x00\x06foobar')
	assert not status.error(), \
		f"{funcname()}: error unflattening(b'\x09\x00\x06foobar'): {status.error()}"
	assert df.type == 'string' and df.value == b'foobar', \
		f"{funcname()}: unflatten(b'\x09\x00\x06foobar') mismatch: {df.value}"

	df.type = 'unknown'
	df.value = None
	status = df.unflatten(b'\x06\x00\x02\x03\xe8')
	assert not status.error(), \
		f"{funcname()}: error unflattening(b'\x06\x00\x02\x03\xe8'): {status.error()}"
	assert df.type == 'uint16' and df.value == b'\x03\xe8', \
		f"{funcname()}: unflatten(b'\x06\x00\x02\x03\xe8') mismatch: {df.value}"


if __name__ == '__main__':
	test_check_range()
	test_set()
	test_get()
	test_get_flat_size()
	test_is_valid()
	test_unflatten_all()
	test_flatten_unflatten()
