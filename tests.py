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
    build_args_str,
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
        self.assertEqual(loglevel_int(None), logging.DEBUG)


def evar_and_param(
    evar_name,
    evar_value,
    logf_param_name,
    logf_param_value,
    ret=1,
    *args,
    **kwargs
):

    def wrapper_env():
        os.environ[evar_name] = evar_value

        @logf()
        def f(*args, **kwargs):
            return ret

        if evar_name in os.environ:
            del os.environ[evar_name]
        return f

    def wrapper_param():
        @logf(**{logf_param_name: logf_param_value})
        def f(*args, **kwargs):
            return ret

        return f

    return wrapper_env, wrapper_param


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
        ef, pf = evar_and_param('LOGF_USE_PRINT', 'True', 'use_print', True)

        for f in [ef(), pf()]:
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
            self.assertEqual(mock_print.call_count, 2)
            self.assertTrue(msg_exit.endswith('1'))
            self.assertIn('f() 0.', msg_exit)

    def test_evar_single_msg(self):
        ef, pf = evar_and_param('LOGF_SINGLE_MSG', 'True', 'single_msg', True)

        outs = []
        for f in [ef(), pf()]:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()
            outs.append(msgs.output)
            msgs = msgs.output

            self.assertTrue(len(msgs) == 1)
            self.assertTrue(msgs[0].endswith('1'))
            self.assertIn('f() 0.', msgs[0])

    def test_evar_max_str_len(self):
        ef, pf = evar_and_param(
            'LOGF_MAX_STR_LEN', '100', 'max_str_len', 100, 'a' * 500
        )

        for f in [ef(), pf()]:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()
            msgs = msgs.output
            self.assertTrue(len(msgs) == 2)
            self.assertTrue(len(msgs[1]) < 200)

    def test_evar_log_args(self):
        ef, pf = evar_and_param(
            'LOGF_LOG_ARGS',
            'False',
            'log_args',
            False,
            1,
            ('arg1', 'arg2'),
            {'kwarg1': 'kwarg2'},
        )

        for f in [ef(), pf()]:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()
            msgs = msgs.output
            self.assertTrue(len(msgs) == 2)
            self.assertIn('f()', msgs[0])
            self.assertIn('f()', msgs[1])
            for _not in ['arg1', 'arg2', 'kwarg1', 'kwarg2']:
                self.assertNotIn(_not, msgs[0])
                self.assertNotIn(_not, msgs[1])

    def test_evar_log_return(self):
        ef, pf = evar_and_param(
            'LOGF_LOG_RETURN', 'False', 'log_return', False, 'returnme'
        )

        for f in [ef(), pf()]:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()
            msgs = msgs.output
            self.assertTrue(len(msgs) == 2)
            self.assertNotIn('returnme', msgs[1])

    def test_evar_log_exec_time(self):
        ef, pf = evar_and_param(
            'LOGF_LOG_EXEC_TIME', 'False', 'log_exec_time', False
        )

        for f in [ef(), pf()]:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()
            msgs = msgs.output
            print(msgs)
            self.assertNotIn('0.', msgs[0])

    def test_evar_use_logger_str(self):
        os.environ['LOGF_USE_LOGGER'] = 'logf'

        @logf()
        def f():
            return 1

        from logfunc.main import getLogger

        with patch('logfunc.main.getLogger') as mock_getLogger:
            with patch('logfunc.main.handle_log') as mock_handle_log:
                mock_getLogger.return_value = 'logf'
                f()

        self.assertTrue(mock_handle_log.call_count > 0)
        self.assertIn(getLogger('logf'), mock_handle_log.call_args_list[0][0])

        @logf(use_logger='logf')
        def f():
            return 1

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with patch('logfunc.main.getLogger') as mock_getLogger:
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


class TestLogfParams(unittest.TestCase):
    def setUp(self):
        clear_env_vars()

    def test_passed_logger(self):
        logger = getLogger('logf')

        @logf(use_logger=logger)
        def f():
            return 1

        with patch('logfunc.main.handle_log') as mock_handle_log:
            f()

        self.assertTrue(mock_handle_log.call_count > 0)
        self.assertIn(logger, mock_handle_log.call_args_list[0][0])

    def test_passed_logger_str(self):
        @logf(use_logger='logf')
        def f():
            return 1

        with patch('logfunc.main.handle_log') as mock_handle_log:
            f()

        self.assertTrue(mock_handle_log.call_count > 0)
        self.assertIn(getLogger('logf'), mock_handle_log.call_args_list[0][0])

    def test_log_exception_false(self):
        @logf(log_exception=False, single_msg=True)
        def f():
            raise ValueError('Test Error')

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                f()

        self.assertTrue(mock_handle_log.call_count == 0)


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

    @async_test
    async def test_async_no_exception(self):
        @logf(log_exception=False, single_msg=True)
        async def async_func():
            raise ValueError('Test Error')

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                await async_func()

        self.assertEqual(mock_handle_log.call_count, 0)


class TestLogfErrorHandling(unittest.TestCase):
    def setUp(self):
        clear_env_vars()
        os.environ['LOGF_SINGLE_EXCEPTION'] = 'False'

    def test_sync_log_exception_true_use_print_true(self):
        @logf(log_exception=True, use_print=True)
        def sync_raise_error():
            raise ValueError("Test Error")

        with patch('logfunc.main.format_exception') as mock_format_exception:
            with self.assertRaises(ValueError):
                sync_raise_error()

        self.assertTrue(mock_format_exception.call_count > 0)

    def test_sync_log_exception_true_use_print_false(self):
        @logf(log_exception=True, use_print=False)
        def sync_raise_error():
            raise ValueError("Test Error")

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                sync_raise_error()

        self.assertTrue(mock_handle_log.call_count > 0)
        self.assertIn('ERROR', mock_handle_log.call_args_list[1][0])

    def test_sync_log_exception_false_use_print_true(self):
        @logf(log_exception=False, use_print=True)
        def sync_raise_error():
            raise ValueError("Test Error")

        with self.assertRaises(ValueError):
            sync_raise_error()

    @async_test
    async def test_async_log_exception_true_use_print_true(self):
        @logf(log_exception=True, use_print=True)
        async def async_raise_error():
            raise ValueError("Async Test Error")

        with patch('logfunc.main.format_exception') as mock_format_exception:
            with self.assertRaises(ValueError):
                await async_raise_error()

        self.assertTrue(mock_format_exception.call_count > 0)

    @async_test
    async def test_async_log_exception_true_use_print_false(self):
        @logf(log_exception=True, use_print=False)
        async def async_raise_error():
            raise ValueError("Async Test Error")

        with self.assertRaises(ValueError), self.assertLogs(
            level='ERROR'
        ) as log:
            await async_raise_error()
        self.assertIn("Async Test Error", log.output[0])


import threading

import logging
import threading
from io import StringIO
from unittest.mock import patch


class TestLogfSingleThreadedExceptionHandling(unittest.TestCase):
    def setUp(self):
        clear_env_vars()
        os.environ['LOGF_SINGLE_MSG'] = 'True'

    def test_single_exception_true(self):

        @logf()
        def function_raises():
            @logf()
            def f2():
                @logf()
                def f3():
                    raise ValueError("Error in f3")

                f3()

            f2()

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                function_raises()

        self.assertEqual(mock_handle_log.call_count, 1)

    def test_single_exception_false(self):

        @logf(single_exception=False, log_exception=True)
        def function_raises():
            @logf(single_exception=False, log_exception=True)
            def f2():
                @logf(single_exception=False, log_exception=True)
                def f3():
                    raise ValueError("Error in f3")

                f3()

            f2()

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                function_raises()

        self.assertEqual(mock_handle_log.call_count, 3)
        self.assertIn('Error in f3', mock_handle_log.call_args_list[0][0][0])
        for i, f in enumerate(['f3', 'f2', 'function_raises']):
            self.assertIn(f, mock_handle_log.call_args_list[i][0][0])


class TestLogfSingleThreadedAsyncExceptionHandling(
    unittest.IsolatedAsyncioTestCase
):
    def setUp(self):
        clear_env_vars()
        os.environ['LOGF_SINGLE_MSG'] = 'True'

    async def test_single_exception_true(self):

        @logf()
        async def function_raises():
            @logf()
            async def f2():
                @logf()
                async def f3():
                    raise ValueError("Error in f3")

                await f3()

            await f2()

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                await function_raises()
        for call in mock_handle_log.call_args_list:
            print(call[0][0])
        self.assertEqual(mock_handle_log.call_count, 1)

    async def test_single_exception_false(self):

        @logf(single_exception=False, log_exception=True)
        async def function_raises():
            @logf(single_exception=False, log_exception=True)
            async def f2():
                @logf(single_exception=False, log_exception=True)
                async def f3():
                    raise ValueError("Error in f3")

                await f3()

            await f2()

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                await function_raises()

        self.assertEqual(mock_handle_log.call_count, 3)
        # Ensure the exception message from the deepest function is logged
        self.assertIn('Error in f3', mock_handle_log.call_args_list[0][0][0])
        # Check that each function's name appears in the log messages
        for i, f in enumerate(['f3', 'f2', 'function_raises']):
            self.assertIn(f, mock_handle_log.call_args_list[i][0][0])


from concurrent.futures import ThreadPoolExecutor, as_completed


class TestLogfMultiThreadedSyncExceptionHandling(unittest.TestCase):
    def setUp(self):
        clear_env_vars()
        os.environ['LOGF_SINGLE_MSG'] = 'True'

    def function_raises_wrapper(self, single_exception):
        @logf(single_exception=single_exception, log_exception=True)
        def function_raises():
            @logf(single_exception=single_exception, log_exception=True)
            def f2():
                @logf(single_exception=single_exception, log_exception=True)
                def f3():
                    raise ValueError("Error in f3")

                f3()

            f2()

        # Note: We don't perform assertion here, just call the function
        function_raises()

    def test_multithreaded_single_exception_true(self):
        expected_count = 1
        results = []
        with patch('logfunc.main.handle_log') as mock_handle_log:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.function_raises_wrapper, True)
                    for _ in range(5)
                ]
                for future in as_completed(futures):
                    # Collect results or exceptions from futures if necessary
                    results.append(future.exception())
            # Perform assertions here in the main thread
            self.assertEqual(mock_handle_log.call_count, expected_count * 5)
            for result in results:
                print(result)

    def test_multithreaded_single_exception_false(self):
        expected_count = 3
        results = []
        with patch('logfunc.main.handle_log') as mock_handle_log:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.function_raises_wrapper, False)
                    for _ in range(5)
                ]
                for future in as_completed(futures):
                    results.append(future.exception())
            self.assertEqual(mock_handle_log.call_count, expected_count * 5)
            for result in results:
                print(result)


class TestLogfRegression(unittest.TestCase):
    def setUp(self):
        clear_env_vars()

    def test_return_not_str(self):
        @logf()
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            ret = f()

        msgs = msgs.output
        self.assertIn('1', msgs[1])
        self.assertEqual(ret, 1)

    def test_error_str_method(self):
        class CustomError(Exception):
            pass

        class StrError:
            def __init__(self):
                pass

            def __str__(self):
                raise CustomError("raise error in __str__")

        @logf()
        def f():
            return StrError()

        with patch('logfunc.main.build_args_str') as mock_build_args_str:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()

        self.assertTrue(mock_build_args_str.call_count > 0)
        self.assertIn('[LOGF STR ERROR', msgs.output[1])
