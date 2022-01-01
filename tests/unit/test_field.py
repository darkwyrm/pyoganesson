import inspect

import pyoganesson.field as field

def funcname() -> str: 
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def test_check_range():
	'''Tests the integer range-checking functions'''

	try:
		field.check_int_range(1,0)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass

	try:
		field.check_int_range(1,128)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass

	try:
		field.check_uint_range(1,0)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass

	try:
		field.check_uint_range(1,128)

		# If the above call fails to throw an exception, then the function has failed this test
		assert False, f"{funcname()}: int range check failed to throw a value exception"
	except ValueError:
		pass
	
	signed_tests = [ (127,8), (32000,16), (70000, 32), (0xFFFFF, 64)]
	for pair in signed_tests:
		assert field.check_int_range(pair[0], pair[1]), \
			"{pair[1]}-bit signed range check failed: {pair[0]}"

	unsigned_tests = [ (250,8), (65000,16), (0x20000, 32), (0x200000000, 64) ]
	for pair in signed_tests:
		assert field.check_uint_range(pair[0], pair[1]), \
			"{pair[1]}-bit signed range check failed: {pair[0]}"



if __name__ == '__main__':
	test_check_range()
