import unittest
import subprocess
import sys

base_args = [sys.executable, 'mathics/kernel.py']
# base_args = ['math']


def new_kernel(args, stdin):
    kernel = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return kernel.communicate(stdin)[0]


class TestKernel(unittest.TestCase):
    """
    Test case for the mathics kernel script
    """

    def test_basic(self):
        self.assertTrue(new_kernel(base_args, '1+1\n').endswith(
            '.\n\nIn[1]:= \nOut[1]= 2\n\nIn[2]:= \n'))

    def test_noprompt(self):
        self.assertEquals(
            new_kernel(base_args+['-noprompt'], '1+1\n'),
            '\n2\n\n')


class TestNotebook(unittest.TestCase):
    """
    Test case for the mathics notebook frontend
    """

    # TODO Using Selenium?


if __name__ == '__main__':
    unittest.main()
