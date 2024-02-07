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
from unittest.mock import MagicMock, patch

from logfunc.main import getLogger, logf

sys.path.append(abspath(dirname(__file__)))

from logfunc.main import (
    EVARS,
    MSG_FORMATS,
    TRUNC_STR_LEN,
    Env,
    handle_log,
    logf,
    loglevel_int,
    trunc_str,
)


def clear_env_vars():
    for evar in EVARS:
        os.environ.pop(evar, None)


class TestUtils(unittest.TestCase):
    def test_loglvl_int(self):
        self.assertEqual(loglevel_int('DEBUG'), logging.DEBUG)
        self.assertEqual(loglevel_int('INFO'), logging.INFO)
        self.assertEqual(loglevel_int('WARNING'), logging.WARNING)
        self.assertEqual(loglevel_int('ERROR'), logging.ERROR)
        self.assertEqual(loglevel_int('CRITICAL'), logging.CRITICAL)
        self.assertEqual(loglevel_int('NOTSET'), logging.NOTSET)
        self.assertEqual(loglevel_int(10), 10)
        self.assertEqual(loglevel_int(), logging.DEBUG)


class TestLogfEnvVars(unittest.TestCase):
    def setUp(self):
        clear_env_vars()

    def test_no_env_vars(self):
        env = Env()
        for evar in EVARS:
            self.assertIsNone(getattr(env, evar))

    def test_defaults(self):
        _long = TRUNC_STR_LEN * 5

        @logf()
        def f(*args, **kwargs):
            return 'r' * _long

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f(1, 2, three='3' * _long, func_return='r' * _long)

        msgs = msgs.output

        self.assertTrue(len(msgs) == 2)
        self.assertIn('f()', msgs[0])
        self.assertIn('f()', msgs[1])
        self.assertIn(str((1, 2)), msgs[0])
        self.assertIn('0.', msgs[1])
        self.assertTrue(len(msgs[1]) < TRUNC_STR_LEN * 2)

    def test_evar_use_print(self):
        os.environ['LOGF_USE_PRINT'] = 'True'

        @logf()
        def f():
            return 1

        with patch('builtins.print') as mock_print:
            f()

        # Replace mock_print.assert_called()
        self.assertTrue(mock_print.call_count > 0)

        msg_enter = mock_print.call_args_list[0][0][0]
        msg_exit = mock_print.call_args_list[1][0][0]
        self.assertEqual(
            msg_enter,
            MSG_FORMATS.enter.format(
                func_name='f', args_str=str(()) + ' ' + str({})
            ),
        )
        self.assertTrue(mock_print.call_count == 2)
        self.assertTrue(msg_exit.endswith('1'))
        self.assertIn('f() 0.', msg_exit)

    def test_evar_single_msg(self):
        os.environ['LOGF_SINGLE_MSG'] = 'True'

        @logf()
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = msgs.output

        self.assertTrue(len(msgs) == 1)
        self.assertTrue(msgs[0].endswith('1'))
        self.assertIn('f() 0.', msgs[0])
        self.assertTrue('()' in msgs[0])

    def test_evar_max_str_len(self):
        os.environ['LOGF_MAX_STR_LEN'] = '10'

        @logf()
        def f():
            return 'a' * 100

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = msgs.output
        self.assertIn('a' * 10 + '...', msgs[1])

    def test_evar_log_args(self):
        os.environ['LOGF_LOG_ARGS'] = 'False'

        @logf()
        def f(*args, **kwargs):
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f('onetwothree')

        msgs = msgs.output
        self.assertNotIn('onetwothree', msgs[0])

    def test_evar_log_return(self):
        os.environ['LOGF_LOG_RETURN'] = 'False'

        @logf(log_return=False)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = msgs.output
        self.assertFalse(msgs[1].endswith('1'))

    def test_evar_log_exec_time(self):
        os.environ['LOGF_LOG_EXEC_TIME'] = 'False'

        @logf(log_exec_time=False)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = msgs.output
        self.assertFalse('0.' in msgs[1])

    def test_evar_use_logger(self):
        os.environ['LOGF_USE_LOGGER'] = 'logf'

        @logf()
        def f():
            return 1

        with patch('logging.Logger.log') as mock_log:
            from logfunc.main import getLogger

            with patch('logfunc.main.getLogger') as mock_getLogger:
                with patch('logfunc.main.handle_log') as mock_handle_log:
                    mock_getLogger.return_value = 'logf'
                    f()

        self.assertTrue(mock_handle_log.call_count > 0)
        self.assertIn(getLogger('logf'), mock_handle_log.call_args_list[0][0])

    def test_evar_stack_info(self):
        os.environ['LOGF_STACK_INFO'] = 'True'

        @logf(log_stack_info=True)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = msgs.output
        self.assertTrue('tests.py' in msgs[0])
        self.assertIn('Stack (most recent call last)', msgs[0])

    def test_log_exception(self):
        os.environ['LOGF_LOG_EXCEPTION'] = 'True'

        @logf(log_exception=True)
        def f():
            pass

        f()

    def test_measure_time(self):

        @logf(measure_time=False)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()

        msgs = msgs.output
        self.assertTrue('0.' not in msgs[1])


# Helper function to run async functions in tests
def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestLogfAsync(unittest.TestCase):
    def setUp(self):
        # Redirect stdout to capture print outputs for tests
        self.held, sys.stdout = sys.stdout, StringIO()

    def tearDown(self):
        # Clean up and restore stdout
        sys.stdout = self.held

    @async_test
    async def test_async_function_logging(self):
        @logf(use_print=True)
        async def async_func(x, y):
            return x + y

        await async_func(1, 2)
        output = sys.stdout.getvalue()
        self.assertIn('async_func()', output)
        self.assertIn('3', output)

    @async_test
    async def test_async_function_logging_with_logger(self):
        @logf(single_msg=True)
        async def async_func(x, y):
            return x + y

        with patch('logfunc.main.handle_log') as mock_handle_log:
            await async_func(1, 2)

        # Replace mock_handle_log.assert_called_once()
        self.assertEqual(mock_handle_log.call_count, 1)

    @async_test
    async def test_async_no_args(self):
        @logf(log_args=False)
        async def async_func(*args):
            return 1

        await async_func('logged')
        output = sys.stdout.getvalue()
        self.assertNotIn('logged', output)
