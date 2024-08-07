#!/usr/bin/env python3
import asyncio
import logging
import os
import re
import sys
import unittest as ut
from io import StringIO
from json import loads
from os.path import abspath, dirname, join
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import MagicMock, patch

import logfunc

from logfunc.main import getLogger, logf

from logfunc.defaults import TRUNC_STR_LEN
from logfunc.main import (
    EVARS,
    MSG_FORMATS,
    handle_log,
    logf,
    Cfg,
    loglevel_int,
    build_argstr,
    trunc_str,
    EXEC_TIME_FMT,
)


def _find_id(msg: str, expected: bool = True) -> str:
    """if expected, asserts id in msg, else assert not in msg"""
    id = re.findall(r'\|([a-zA-Z0-9-_]*)', msg)

    if expected:
        print(msg, id)
        assert len(id) >= 1
        return id[0]
    assert len(id) == 0


def clear_env_vars():
    for evar in EVARS:
        os.environ.pop(evar[0], None)


class TestUtils(ut.TestCase):
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

    def test_build_argstr_trunc(self):
        @logf(max_str_len=5)
        def f(*args, **kwargs):
            return 1

        with self.assertLogs(level=logging.DEBUG) as lg:
            f(
                'a' * 100000,
                'short',
                'longlonglonglongtrunc',
                b='b' * 10000,
                b2='betwo',
            )
        out = lg.output
        self.assertIn('betwo', ''.join(out))


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

        @logf(identifier=False)
        def f(*args, **kwargs):
            return ret

        if evar_name in os.environ:
            del os.environ[evar_name]
        return f

    def wrapper_param():
        @logf(**{logf_param_name: logf_param_value}, identifier=False)
        def f(*args, **kwargs):
            return ret

        return f

    return wrapper_env, wrapper_param


class TestLogfEnvVars(ut.TestCase):
    def setUp(self):
        clear_env_vars()

    def test_cfg_evars(self):
        for evtup in EVARS:
            evar, eattr, ekwarg, edef = evtup
            c = Cfg()
            self.assertEqual(getattr(c, eattr), edef)

    def test_cfg_evars_overrides(self):
        for evtup in EVARS:
            evar, eattr, ekwarg, edef = evtup
            c = Cfg(**{ekwarg: 'test'})
            self.assertEqual(getattr(c, eattr), 'test')

            if isinstance(edef, bool):
                os.environ[evar] = 'True'

                c = Cfg()
                self.assertEqual(getattr(c, eattr), True)

                os.environ[evar] = 'False'
                c = Cfg()
                self.assertEqual(getattr(c, eattr), False)
            elif evar == 'LOGF_USE_LOGGER':
                os.environ[evar] = 'test'
                with patch('logfunc.config.getLogger') as mock_getLogger:
                    c = Cfg()
                    self.assertEqual(
                        getattr(c, eattr), mock_getLogger.return_value
                    )
                    self.assertTrue(mock_getLogger.call_count > 0)
                    self.assertIn('test', mock_getLogger.call_args[0])
            elif evar == 'LOGF_MAX_STR_LEN':
                os.environ[evar] = '100'
                c = Cfg()
                self.assertEqual(getattr(c, eattr), 100)
                os.environ[evar] = 'None'
                c = Cfg()
                self.assertEqual(getattr(c, eattr), None)

            else:
                os.environ[evar] = 'test'
                c = Cfg()
                self.assertEqual(getattr(c, eattr), 'test')

    def test_defaults(self):
        _long = TRUNC_STR_LEN * 5

        @logf()
        def f(*args, **kwargs):
            return 'r' * _long

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f(1, 2, three='3' * _long, func_return='r' * _long)

        msgs = msgs.output

        self.assertTrue(len(msgs) == 2)

        # enter/exit
        for i, m in enumerate(msgs[0:2]):

            _find_id(m)

            if i == 0:
                self.assertIn('->', m)
                self.assertIn(str((1, 2)), m)
            else:
                self.assertIn('<-', m)
                self.assertIn('0.', m)
                self.assertTrue(len(m) < TRUNC_STR_LEN * 2)

    def test_evar_use_print(self):
        ef, pf = evar_and_param('LOGF_USE_PRINT', 'True', 'use_print', True)

        for f in [ef(), pf()]:
            with patch('builtins.print') as mock_print:
                f()

            # Replace mock_print.assert_called()
            self.assertTrue(mock_print.call_count > 0)

            msg_enter = mock_print.call_args_list[0][0][0]
            msg_exit = mock_print.call_args_list[1][0][0]
            print(msg_enter, msg_exit)
            self.assertEqual(mock_print.call_count, 2)
            self.assertTrue(msg_exit.endswith('1'))
            self.assertIn('f 0.', msg_exit)

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
            self.assertNotIn('->', msgs[0])
            self.assertNotIn('<-', msgs[0])
            self.assertEqual(msgs[0][-1], '1')

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
            self.assertIn(' f ', msgs[0])
            self.assertIn(' f ', msgs[1])
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

    def test_measure_time(self):

        @logf(measure_time=False)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()

        msgs = msgs.output
        self.assertTrue('0.' not in msgs[1])

    def test_log_under_logf_log_level(self):
        os.environ['LOGF_LOG_LEVEL'] = 'INFO'

        @logf(level='DEBUG')
        def f():
            return 1

        @logf(level='INFO')
        def f2():
            return 1

        if sys.version_info.minor > 9:
            print('Testing for Python 3.8+', sys.version, sys.version_info)
            with self.assertNoLogs(level=logging.DEBUG):
                f()
        else:
            _err = False
            try:
                with self.assertLogs(level=logging.DEBUG):
                    f()
            except AssertionError:
                _err = True

            self.assertTrue(_err)

        with self.assertLogs(level=logging.INFO):
            f2()

    def test_identifier_evar(self):

        os.environ['LOGF_IDENTIFIER'] = 'False'

        @logf(identifier=True)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = '\n'.join(msgs.output)

        self.assertEqual(len(re.findall(r'<-|->\|', msgs)), 2)
        del os.environ['LOGF_IDENTIFIER']

        @logf(identifier=True)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()
        msgs = '\n'.join(msgs.output)
        self.assertEqual(len(re.findall(r'<-|->\|[^ ]+', msgs)), 2)


class TestLogfParams(ut.TestCase):
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

    def test_single_msg_identifier(self):
        @logf(single_msg=True)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()

        msgs = msgs.output
        self.assertTrue(len(msgs) == 1)
        msg = msgs[0]
        self.assertTrue(msg.endswith('1'))
        self.assertNotIn('->', msgs[0])
        self.assertNotIn('<-', msgs[0])
        self.assertEqual(re.findall(r'\[([a-zA-Z0-9-_]*)\]', msg), [])

    def test_stack_info(self):
        @logf(log_stack_info=True)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()

        msgs = msgs.output
        self.assertTrue(len(msgs) == 2)
        self.assertIn('logfunc/main.py', msgs[0])
        self.assertIn('logfunc/main.py', msgs[1])

    def test_log_stack(self):
        """for 100% coverage"""
        os.environ['LOGF_STACK_INFO'] = 'True'
        c = Cfg(log_stack_info=False)
        self.assertTrue(c.log_stack)


# Helper function to run async functions in tests
def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestLogfAsync(ut.TestCase):
    def setUp(self):
        # Redirect stdout to capture print outputs for tests
        self.held, sys.stdout = sys.stdout, StringIO()

    def tearDown(self):
        # Clean up and restore stdout
        sys.stdout = self.held

    @async_test
    async def test_async_function_logging(self):
        @logf(use_print=True, identifier=False)
        async def async_func(x, y):
            return x + y

        await async_func(1, 2)
        output = sys.stdout.getvalue()
        self.assertIn('async_func ', output)
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


if sys.version_info >= (3, 8):

    class TestLogfSingleThreadedAsyncExceptioIsolatedAnHandling(
        ut.IsolatedAsyncioTestCase
    ):
        # replace with IsolatedAsyncioTestCase on 3.5+
        def setUp(self):
            clear_env_vars()
            os.environ['LOGF_SINGLE_MSG'] = 'True'


from concurrent.futures import ThreadPoolExecutor, as_completed


class TestLogfMultiThreadedSyncExceptionHandling(ut.TestCase):
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

        with patch('logfunc.main.handle_log') as mock_handle_log:
            with self.assertRaises(ValueError):
                function_raises()

        self.assertEqual(mock_handle_log.call_count, 1)


class TestLogfRegression(ut.TestCase):
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

        with patch('logfunc.main.build_argstr') as mock__argstr:
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()

        self.assertTrue(mock__argstr.call_count > 0)
        self.assertIn('[LOGF STR ERROR', msgs.output[1])

    def test_unique_ids(self):
        @logf(identifier=True)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()

        msgs = msgs.output

        id1, id2 = _find_id(msgs[0]), _find_id(msgs[1])
        self.assertEqual(id1, id2)

        with self.assertLogs(level=logging.DEBUG) as msgs:
            f()

        msgs = msgs.output
        id1 = _find_id(msgs[0])
        self.assertNotEqual(id1, id2)

    def test_unique_ids_false(self):
        @logf(identifier=False)
        def f():
            return 1

        with patch('logfunc.main._get_id', lambda x: '__TEST__'):
            with self.assertLogs(level=logging.DEBUG) as msgs:
                f()
        self.assertNotIn('__TEST__', ' '.join(msgs.output))


class LogTestCase(ut.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_logout(self: 'LogTestCase', f, level=logging.DEBUG) -> List[str]:
        with self.assertLogs(level=level) as l:
            f()
        return l.output


class TestLogfClassInit(LogTestCase):
    _kw = {'use_print': True}

    def setUp(self):
        clear_env_vars()

    def test_class_init(self):
        class Test:
            init = False

            @logf(**self._kw)
            def __init__(self, *args, **kwargs):
                self.init = True

        class Test2:
            class Test3:
                @logf(**self._kw)
                def __init__(self):
                    self.test = Test()

            def t(t3=Test3):
                t4 = t3()

                def f():
                    return [t4, t3()]

                t4t3 = f()
                return t4t3

            @logf(**self._kw)
            def __init__(self, t=t()[0]):
                t4 = t

        t2 = Test2()

        t = Test()
        t.t2 = Test2()

    @logf(single_msg=True, use_print=True)
    def test_single_msg(self):
        return 1

    def test_format(self):
        @logf(log_args=False)
        def f():
            return 1

        with self.assertLogs(level=logging.DEBUG) as l:
            f()

        out = self.get_logout(f)
