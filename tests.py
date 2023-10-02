#!/usr/bin/env python3
import asyncio
import logging
import os
import re
import sys
import unittest
from io import StringIO
from json import loads
from os.path import abspath, dirname, join
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import patch

sys.path.append(abspath(dirname(__file__)))

from logfunc.config import EVARS
from logfunc.main import TRUNC_STR_LEN, logf
from logfunc.utils import (
    func_args_str,
    func_return_str,
    get_evar,
    loglevel_int,
    parse_logmsg,
    print_or_log,
    trunc_str,
)

logging.basicConfig(level=logging.DEBUG)

for evar in EVARS:
    if evar in os.environ:
        del os.environ[evar]


TESTFNAME = 'funcname'
TESTRET = 'ret'
TESTARGSTR = "(1, 2.5) {'a': 3.5}"
TESTARGS = (1, 2.5)
TESTKWARGS = {'a': 3.5}


@logf()
def testsyncfunc(*args, **kwargs):
    return TESTRET


@logf()
async def testasyncfunc(*args, **kwargs):
    return TESTRET


# Synchronous decorator
def sync_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Starting {func.__name__}...")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}.")
        return result

    return wrapper


@sync_decorator
def my_func(x):
    print(f"Running function with argument {x}")


# Asynchronous decorator
def async_decorator(async_func):
    async def async_wrapper(*args, **kwargs):
        print(f"Starting {async_func.__name__}...")
        result = await async_func(*args, **kwargs)
        print(f"Finished {async_func.__name__}.")
        return result

    return async_wrapper


class TestLogf(unittest.TestCase):
    """inherits from unittest.TestCase to test @logf() decorator"""

    @classmethod
    def setUpClass(cls):
        for evar in EVARS:
            if evar in os.environ:
                del os.environ[evar]

    @staticmethod
    def _parse_log(log_message: str) -> dict:
        """Parse a log message using regex."""
        pattern = (
            r'(?P<loglevel>\w+):'
            r'(?P<funcname>\w+\(\)) '
            r'(?:\| (?P<argstr>[^|]*) )?'
            r'(?:\| (?P<result>[^|]*) )?'
            r'(?:\| (?P<exectime>\S+))?'
        )
        match = re.match(pattern, log_message)
        return match.groupdict() if match else {}

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

        with self.assertLogs(level='DEBUG') as log:
            testsyncfunc(*TESTARGS, **TESTKWARGS)

        self.assertTrue(len(log.output) == 2)

        msgs = [parse_logmsg(x) for x in log.output]

        self.assertTrue(msgs[0]['loglevel'] == 'DEBUG')
        self.assertTrue(msgs[0]['funcname'] == 'testsyncfunc()')
        self.assertTrue(msgs[0]['argstr'] == TESTARGSTR)
        self.assertTrue(msgs[1]['result'] == TESTRET)
        self.assertTrue(msgs[1]['exectime'] != '')

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

    def test_nested_function(self):
        """Tests decorator on a function nested within another function."""

        @logf()
        def outer():
            @logf()
            def inner(x):
                return x * 2

            return inner(5)

        with self.assertLogs(level='DEBUG') as log:
            result = outer()
            self.assertEqual(result, 10)
            self.assertTrue(
                len(log.output) >= 4
            )  # Two logs each for inner and outer

    def test_exception(self):
        """Tests that an exception raised in a decorated function is properly logged."""

        @logf()
        def raise_exception():
            raise ValueError("Test exception")

        with self.assertLogs(level='DEBUG') as log:
            with self.assertRaises(ValueError):
                raise_exception()
            pmsg = parse_logmsg(log.output[0])
            self.assertEqual(pmsg['loglevel'], 'DEBUG')
            self.assertEqual(pmsg['loggername'], 'root')
            self.assertEqual(pmsg['funcname'], 'raise_exception()')
            self.assertEqual(len(log.output), 1)

    def test_class_method(self):
        """Tests decorator on a class method."""

        class TestClass:
            @logf()
            def class_method(self, x, y=2):
                return x * 3

        obj = TestClass()

        with self.assertLogs(level='DEBUG') as log:
            obj.class_method(999, y=2)
            pmsg = parse_logmsg(log.output[0])

            self.assertEqual(pmsg['loglevel'], 'DEBUG')
            self.assertEqual(pmsg['loggername'], 'root')
            self.assertEqual(pmsg['funcname'], 'class_method()')
            self.assertTrue(pmsg['argstr'].find('999') != -1)
            self.assertTrue(pmsg['argstr'].find("{'y': 2}"))

    def test_sync_funcname_format(self):
        """Regression tests for bug where () is not in func names in logs"""

        @logf()
        def funcname():
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            funcname()
            out = [l for l in log.output if '%s()' % TESTFNAME in l]
            aout = [l for l in log.output if 'async %s()' % TESTFNAME in l]
            self.assertTrue(len(out) > 0)
            self.assertTrue(len(aout) == 0)


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

    def test_async_exception(self):
        """Tests that an exception raised in a decorated async function is properly logged."""

        @logf()
        async def async_raise_exception():
            raise ValueError("Async test exception")

        with self.assertLogs(level='DEBUG') as log:
            with self.assertRaises(ValueError):
                asyncio.run(async_raise_exception())
            print(log.output, file=sys.stderr)
            self.assertTrue(len(log.output) <= 2)
            self.assertTrue(
                'async async_raise_exception()' in ''.join(log.output)
            )
            self.assertTrue('ValueError' not in ''.join(log.output))

    def test_async_class_method(self):
        """Tests decorator on an asynchronous class method."""

        class AsyncTestClass:
            @logf()
            async def async_class_method(self, x):
                await asyncio.sleep(0.1)
                return x * 3

        obj = AsyncTestClass()

        with self.assertLogs(level='DEBUG') as log:
            result = asyncio.run(obj.async_class_method(3))
            self.assertEqual(result, 9)
            self.assertTrue(len(log.output) >= 2)

    def test_async_nested_function(self):
        """Tests decorator on an asynchronous function nested within another function."""

        @logf()
        @async_decorator
        async def my_async_func(x):
            await asyncio.sleep(x)
            print(f"Slept for {x} seconds")
            return str(x)

        with self.assertLogs(level='DEBUG') as log:
            print("Running my_async_func...")
            result = asyncio.run(my_async_func(1))
            self.assertTrue(result == '1')
            print(log.output, 'with', result)

    def test_async_in_funcname(self):
        @logf()
        @async_decorator
        async def afunc(x):
            await asyncio.sleep(x)
            print(f"Slept for {x} seconds")
            return str(x)

        with self.assertLogs(level='DEBUG') as log:
            print("Running afunc...")
            result = asyncio.run(afunc(1))
            for l in log.output:
                if l.find('afunc()') != -1:
                    self.assertTrue('async afunc()' in l)


class TestRegressions(unittest.TestCase):
    def test_sync_start_time(self):
        """Tests the sync funcname() logmsg format equivalent"""

        @logf()
        def funcname():
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            funcname()
            self.assertTrue(len(log.output) >= 2)
            timere = r'\d+?\.?\d+s'
            for logmsg in log.output:
                logmsgtime = re.findall(timere, logmsg)
                if len(logmsgtime) > 0:
                    self.assertTrue(len(logmsgtime) == 1)
                    exectime = float(logmsgtime[0].rstrip('s'))
                    self.assertTrue(exectime >= 0.0)
                    self.assertTrue(len(str(exectime)) <= 8)
                    self.assertTrue(exectime <= 20.0)

    def test_async_start_time(self):
        """Tests the async logmsg format equivalent"""

        @logf()
        async def asyncfunc():
            await asyncio.sleep(0.1)
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            asyncio.run(asyncfunc())
            self.assertTrue(len(log.output) >= 2)
            timere = r'\d+?\.?\d+s'
            for logmsg in log.output:
                logmsgtime = re.findall(timere, logmsg)
                if len(logmsgtime) > 0:
                    self.assertTrue(len(logmsgtime) == 1)
                    exectime = float(logmsgtime[0].rstrip('s'))
                    self.assertTrue(len(str(exectime)) <= 8)
                    self.assertTrue(exectime >= 0.1)
                    self.assertTrue(exectime <= 20.0)

    def test_async_funcname_format(self):
        """Regression tests for bug where () is not in func names in logs"""

        @logf()
        async def funcname():
            await asyncio.sleep(0.1)
            return 'ret'

        with self.assertLogs(level='DEBUG') as log:
            retstr = asyncio.run(funcname())
            out = [l for l in log.output if '%s()' % TESTFNAME in l]
            aout = [l for l in log.output if 'async %s()' % TESTFNAME in l]

            self.assertEqual(len(out), len(aout))


class TestUtils(unittest.TestCase):
    def setUp(self):
        # This will store the current environment variables so they can be restored later
        self._original_environ = dict(os.environ)

    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_get_evar(self):
        os.environ['LOGF_LEVEL'] = 'INFO'
        result = get_evar('LOGF_LEVEL', None)
        self.assertEqual(result, 'INFO')

        os.environ['LOGF_MAX_STR_LEN'] = '500'
        result = get_evar('LOGF_MAX_STR_LEN', 1000)
        self.assertEqual(result, 500)

        os.environ['LOGF_SINGLE_MSG'] = 'TRUE'
        result = get_evar('LOGF_SINGLE_MSG', False)
        self.assertTrue(result)

    def test_trunc_str(self):
        result = trunc_str("abcdef", 3)
        self.assertEqual(result, "abc...")

        result = trunc_str("abcdef", 10)
        self.assertEqual(result, "abcdef")

        # regression test for non-strs being provided
        result = trunc_str({1, 2, 3, 4})
        self.assertEqual(result, str({1, 2, 3, 4}))

        # regression test for max_len=None w/ long length
        longstr = 'a' * 1000000
        result = trunc_str(longstr, None)
        self.assertEqual(len(result), len(longstr))

        _milstr = 'a' * 1000000
        _sublen = 20000
        _submilstr = ('a' * _sublen) + '...'

        # test for max_len that is large but not None
        result = trunc_str(_milstr, _sublen)
        self.assertEqual(len(result), len(_submilstr))

    def test_func_args_str(self):
        result = func_args_str("func_name", (1, 2.5), {"a": 3}, True)
        self.assertEqual(result, 'func_name() | (1, 2.5) {\'a\': 3}')

    def test_func_return_str(self):
        result = func_return_str(
            "func_name",
            (1, 2.5),
            {"a": 3.5},
            "Result",
            1629210460.0,
            True,
            True,
            True,
            10,
        )
        # Validate the floating point precision
        print(result, file=sys.stderr)
        self.assertTrue('func_name()' in result)
        self.assertTrue("2.5" in result)
        self.assertTrue("3.5" in result)

    def test_loglevel_int(self):
        result = loglevel_int("DEBUG")
        self.assertEqual(result, 10)  # 10 corresponds to DEBUG level

        result = loglevel_int(20)
        self.assertEqual(result, 20)

    @patch('logging.log')
    def test_print_or_log_use_log(self, mock_log):
        print_or_log("Test Message", level="DEBUG")
        mock_log.assert_called_once()

    def test_parse_logmsgs(self):
        s1 = "funcname() 65345663.00156s | (1, 2.5) {'a': 3.5} | Result"
        s2 = "DEBUG:root:" + s1
        result = parse_logmsg(s1)
        self.assertEqual(result['loglevel'], '')
        self.assertEqual(result['loggername'], '')
        self.assertEqual(result['funcname'], 'funcname()')
        self.assertEqual(result['exectime'], '65345663.00156')
        self.assertEqual(result['argstr'], '(1, 2.5) {\'a\': 3.5}')
        self.assertEqual(result['result'], 'Result')

        result = parse_logmsg(s2)
        self.assertEqual(result['loglevel'], 'DEBUG')
        self.assertTrue(result['loggername'] != '')


if __name__ == '__main__':
    unittest.main()
