#!/usr/bin/env python3
import unittest
import logging
import re
from logfunc import logf

logging.basicConfig(level=logging.DEBUG)

class TestLogf(unittest.TestCase):
    """ inherits from unittest.TestCase to test @logf() decorator """

    def test_defaults(self):
        """
        test_defaults method tests the default behavior of the logf function decorator.

        The test creates a dummy function 'testfunc' decorated by logf and
        checks whether the function arguments, execution time, and return value
        are properly logged at the DEBUG level.

        The log output is checked using the unittest's assertLogs context manager,
        which provides the log records created in its context.

        Asserts:
            - Log level of the first log record is DEBUG.
            - The function name logged is 'testfunc'.
            - The logged arguments match the ones passed to 'testfunc'.
            - The execution time is logged in seconds.
            - The return value of 'testfunc' is logged as 'ret'.
            - The default truncated length of args/kwargs/return
        """
        @logf()
        def testfunc(ar, kar=None):
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            testfunc('ar', kar='kar')

        l0, l1 = log.output[0], log.output[1]

        self.assertTrue(l0.split(':')[0] == 'DEBUG')
        self.assertTrue(l0.split(':')[2].startswith('testfunc'))
        self.assertTrue(re.search(
            r'''\(['"]ar['"],\) {['"]kar['"]: ['"]kar['"]}''',  l0.split(' | ')[1]))

        self.assertIsNotNone(re.search(r'\d+?\.?\d+s', l1.split()[1]))
        self.assertTrue(l1.split(' | ')[1] == 'ret')

        @logf(max_str_len=None)
        def testtrunc():
            return '0' * 1000

        with self.assertLogs(level='DEBUG') as log:
            testtrunc()
            self.assertTrue(
                len(log.output[1].split(' | ')[1]) == 1000)

    def test_max_str_len(self):
        """ tests to ensure that log messages have proper trunc behaviour """
        @logf(max_str_len=10)
        def trunc10():
            return '0' * 1000

        @logf(max_str_len=None)
        def truncNone():
            return '0' * 10000

        with self.assertLogs(level='DEBUG') as log:
            trunc10()
            self.assertTrue(len(log.output[1].split(' | ')[1]) == 10)

        with self.assertLogs(level='DEBUG') as log:
            truncNone()
            self.assertTrue(len(log.output[1].split(' | ')[1]) == 10000)

    def test_measure_time(self):
        """ tests backwards compatability of measure_time kwarg """
        @logf(measure_time=False)
        def notime():
            return 'ret'

        @logf(measure_time=True)
        def hastime():
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            notime()
            self.assertTrue(len(log.output[1].split(' | ')[0].split()) == 1)

        with self.assertLogs(level='DEBUG') as log:
            hastime()
            self.assertTrue(len(log.output[1].split(' | ')[0].split()) == 2)


if __name__ == '__main__':
    unittest.main()
