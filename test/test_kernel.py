import sys
import unittest
import subprocess


base_args = [sys.executable, 'mathics/kernel.py', '-noprompt']


class TestKernel(unittest.TestCase):
    def setUp(self):
        pass

    def test_setup(self):
        #assert self.kernel.communicate('1+1') == ('2', '')
        pass


if __name__ == '__main__':
    unittest.main()
