#!/usr/bin/env python3
import unittest
import logging
import re
import os
import sys
import asyncio
from io import StringIO
from logfunc.main import logf, TRUNC_STR_LEN
from unittest.mock import patch

logging.basicConfig(level=logging.DEBUG)


class TestLogf(unittest.TestCase):
    """inherits from unittest.TestCase to test @logf() decorator"""

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
            - Two log messages are logged by default
        """

        @logf()
        def testfunc(ar, kar=None):
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            testfunc('ar', kar='kar')

        self.assertTrue(len(log.output) == 2)

        l0, l1 = log.output[0], log.output[1]

        self.assertTrue(l0.split(':')[0] == 'DEBUG')
        self.assertTrue(l0.split(':')[2].startswith('testfunc'))
        self.assertTrue(
            re.search(
                r'''\(['"]ar['"],\) {['"]kar['"]: ['"]kar['"]}''',
                l0.split(' | ')[1],
            )
        )

        self.assertIsNotNone(re.search(r'\d+?\.?\d+s', l1.split()[1]))
        self.assertTrue(l1.split(' | ')[1] == 'ret')

        @logf()
        def testtrunc():
            return '0' * 1000000000

        with self.assertLogs(level='DEBUG') as log:
            testtrunc()
            self.assertTrue(
                len(log.output[1].split(' | ')[1]) == TRUNC_STR_LEN + 3
            )

    def test_max_str_len(self):
        """tests to ensure that log messages have proper trunc behaviour"""

        @logf(max_str_len=22)
        def trunc22():
            return '0' * 1000000

        @logf(max_str_len=None)
        def truncNone():
            return '0' * 1000000

        with self.assertLogs(level='DEBUG') as log:
            trunc22()
            self.assertTrue(
                len(log.output[1].split(' | ')[1]) == 22 + 3
            )  # trunc'd by trunc_str

        with self.assertLogs(level='DEBUG') as log:
            truncNone()
            self.assertTrue(len(log.output[1].split(' | ')[1]) == 1000000)

    def test_measure_time(self):
        """tests backwards compatability of measure_time kwarg as well as exec_time"""

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

    def test_single_msg(self):
        """tests single_msg=True only sends a single log message and that it is formatted correctly"""

        @logf(single_msg=True)
        def msg(ar, kar='kar'):
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            msg('ar', kar='kar')

        l0 = log.output[0]

        self.assertTrue(
            re.search(
                r'''\(['"]ar['"],\) {['"]kar['"]: ['"]kar['"]}''',
                l0.split(' | ')[1],
            )
        )
        self.assertIsNotNone(re.search(r'\d+?\.?\d+s', l0.split()[1]))
        self.assertTrue(l0.split(' | ')[2] == 'ret')

    def test_evar_level(self):
        """tests LOGF_LEVEL env var behaviour with logf"""
        os.environ['LOGF_LEVEL'] = 'warning'

        @logf()
        def warn():
            return 'ret'

        with self.assertLogs(level='WARNING') as log:
            warn()

        self.assertTrue(log.output[0].startswith('WARNING'))
        del os.environ['LOGF_LEVEL']

    def test_evar_max_str_len(self):
        """tests LOGF_MAX_STR_LEN behaviour"""
        os.environ['LOGF_MAX_STR_LEN'] = 'NonE'

        @logf()
        def longstr():
            return '0' * 100000

        with self.assertLogs(level='DEBUG') as log:
            longstr()
            self.assertTrue(len(log.output[1]) >= 10000)
        del os.environ['LOGF_MAX_STR_LEN']

        os.environ['LOGF_MAX_STR_LEN'] = '1'

        @logf()
        def longstr():
            return '0' * 100000

        with self.assertLogs(level='DEBUG') as log:
            longstr()
            self.assertTrue(log.output[1].split(' | ')[1] == '0...')
        del os.environ['LOGF_MAX_STR_LEN']

    def test_evar_single_msg(self):
        """tests LOGF_SINGLE_MSG evar override"""
        os.environ['LOGF_SINGLE_MSG'] = 'TruE'

        @logf()
        def singlemsg():
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            singlemsg()
            self.assertEqual(len(log.output), 1)
        del os.environ['LOGF_SINGLE_MSG']

    def test_evar_use_print(self):
        """tests LOGF_USE_PRINT evar override"""
        os.environ['LOGF_USE_PRINT'] = 'True'

        @logf()
        def useprint():
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            useprint()
            for _ in range(5):
                logging.debug('test')
            self.assertEqual(len(log.output), 5)
        del os.environ['LOGF_USE_PRINT']


class TestAsyncLogf(unittest.TestCase):
    """verifies decorator works with async fucns"""

    def test_async(self):
        """tests async function logging"""

        @logf()
        async def asyncfunc():
            await asyncio.sleep(1)
            return 'ret2'

        with self.assertLogs(level='DEBUG') as log:
            asyncio.run(asyncfunc())
            out = [l for l in log.output if 'asyncfunc' in l]
            self.assertTrue(len(out) >= 2)
            self.assertTrue(out[1].split(' | ')[1] == 'ret2')


if __name__ == '__main__':
    unittest.main()
