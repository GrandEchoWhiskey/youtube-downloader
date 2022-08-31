from cgi import test
from cgitb import reset
import unittest
import options
import sys

class TestSum_option(unittest.TestCase):

	def test_init(self):
		
		def test_func(): pass

		opt1 = options._option('a', 'alpha')
		opt2 = options._option('b', 'bravo', test_func)
		self.assertEqual(opt1._option__short, 'a')
		self.assertEqual(opt1._option__long, 'alpha')
		self.assertEqual(opt1._option__func, ())
		self.assertEqual(opt2._option__short, 'b')
		self.assertEqual(opt2._option__long, 'bravo')
		self.assertEqual(opt2._option__func, test_func)

	def test_get(self):

		class test_class:

			def test_method(self): pass

			option = options._option('c', 'charlie', test_method)

		self.assertEqual(test_class.option, {
				"long": 'charlie',
				"short": 'c',
				"function": test_class.test_method
			})

	def test_str(self):

		def test_func(arg1: "arg1", space: "sp ace", optional: "[optional]" = 0):
			"""
			Hidden Above
			HELP: Get delta of a function
			Hidden Below
			Some other function docs ..
			"""
			pass

		opt = options._option('d', 'delta', test_func)

		string = f"{'-d arg1 sp-ace [optional]'.ljust(options.SHORT_JUST, ' ')} | "
		string += f"{'--delta arg1 sp-ace [optional]'.ljust(options.LONG_JUST, ' ')} | "
		string += "Get delta of a function"

		self.assertEqual(str(opt), string)

	def test_min_args(self):

		def test_func1(arg1: "arg1", optional: "[optional]" = 0): pass
		def test_func2(arg1: "arg1", optional: "not optional"): pass

		self.assertEqual(options._option('e', 'echo', test_func1).num_args_min, 1)
		self.assertEqual(options._option('f', 'foxtrot', test_func2).num_args_min, 2)

	def test_min_args(self):

		def test_func1(arg1: "arg1", optional: "[optional]" = 0): pass
		def test_func2(arg1: "arg1", optional: "not optional"): pass

		self.assertEqual(options._option('g', 'golf', test_func1).num_args_max, 2)
		self.assertEqual(options._option('h', 'hotel', test_func2).num_args_max, 2)

	def test_eq(self):

		self.assertTrue(options._option('i', 'india') == options._option('i', 'india'))

	def test_ne(self):

		self.assertTrue(options._option('j', 'juliett') != options._option('k', 'kilo'))


class TestSum_translator(unittest.TestCase):

	def test_add(self):

		tsl = options._translator()

		tsl.add(options._option('l', 'lima'))

		self.assertEqual(tsl.options[0], options._option('l', 'lima'))

	def test_len(self):

		tsl = options._translator()

		tsl._translator__options = list(range(10))

		self.assertEqual(len(tsl), 10)

	def test_next(self):

		tsl = options._translator()

		tsl.add(options._option('m', 'mike'))
		tsl.n = 0

		self.assertEqual(next(tsl), options._option('m', 'mike'))
		self.assertRaises(StopIteration, next, tsl)

	def test_iter(self):

		tsl = options._translator()

		option_list = [
			options._option('n', 'november'),
			options._option('o', 'oscar')
		]

		for item in option_list:
			tsl.add(item)

		for i, option in enumerate(tsl):
			self.assertEqual(option, option_list[i])

		self.assertRaises(StopIteration, next, tsl)

	def test_find_char(self):

		tsl = options._translator()

		tsl.add(options._option('p', 'papa'))
		tsl.add(options._option('q', 'quebec'))

		self.assertEqual(tsl.find_char('q'), options._option('q', 'quebec'))

	def test_find_str(self):

		tsl = options._translator()

		tsl.add(options._option('r', 'romeo'))
		tsl.add(options._option('s', 'sierra'))

		self.assertEqual(tsl.find_str('sierra'), options._option('s', 'sierra'))

	def test_find_fnc(self):

		def test_func1(): pass
		def test_func2(): pass

		tsl = options._translator()

		tsl.add(options._option('t', 'tango', test_func1))
		tsl.add(options._option('u', 'uniform', test_func2))

		self.assertEqual(tsl.find_fnc(test_func1), options._option('t', 'tango', test_func1))

	def test_translate(self):
		
		# Skipping 'python3' because in default it is not in sys.argv
		sys.argv = "test.py -v 10 5 -w 1 -x".split(' ')

		def test_v_func(arg1: 'arg1', arg2: 'arg2'): pass
		def test_w_func(arg1: 'arg1'): pass
		def test_x_func(arg1: '[arg1]' = 0): pass

		tsl = options._translator()

		tsl.add(options._option('v', 'victor', test_v_func))
		tsl.add(options._option('w', 'whiskey', test_w_func))
		tsl.add(options._option('x', 'xray', test_x_func))

		tsl.translate()

		self.assertEqual(tsl._translator__fncargs, {
			'victor': ['10', '5'],
			'whiskey': ['1'],
			'xray': []
		})

		sys.argv = "test.py -a".split(' ')
		tsl = options._translator()
		self.assertRaisesRegex(SystemExit, "No option named: -a", tsl.translate)

	def test_run(self):

		sys.argv = "test.py -y 10".split(' ')

		my_result = 0

		def test_y_func1(arg1: 'arg1', arg2: '[arg2]' = 10):
			nonlocal my_result
			my_result = int(arg1) * int(arg2)

		def test_y_func2(): pass

		tsl1 = options._translator()
		tsl2 = options._translator()

		tsl1.add(options._option('y', 'yankee', test_y_func1))
		tsl2.add(options._option('y', 'yankee', test_y_func2))

		tsl1.translate()
		tsl2.translate()

		tsl1.run()

		self.assertRaises(SystemExit, tsl2.run)

		self.assertEqual(my_result, 100)

	
class TestSum_other(unittest.TestCase):

	def test_add(self):

		options.add('z', 'zulu')

		self.assertTrue(options._option('z', 'zulu') in options._t.options)

	def test_help(self):

		sys.argv = "test.py -h".split(' ')

		self.assertRaisesRegex(SystemExit, f"{options.HELP_NOTE}\nOPTIONS:\n{str(options._t.options[0])}", options.exec)


if __name__ == "__main__":
	unittest.main()