import unittest
import options
import sys

class TestSum_option(unittest.TestCase):

	def test_test(self):
		sys.agrv = "python3 app.py -h"
		options.exec()
		self.assertEqual(len(options._options__t.options), 1)
		
if __name__ == "__main__":
	unittest.main()