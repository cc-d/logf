import os
from typing import Optional as Opt, Union
from logging import getLogger


EVARS = (
    'LOGF_USE_PRINT',
    'LOGF_SINGLE_MSG',
    'LOGF_MAX_STR_LEN',
    'LOGF_LEVEL',
    'LOGF_LOG_ARGS',
    'LOGF_LOG_RETURN',
    'LOGF_LOG_EXEC_TIME',
    'LOGF_USE_LOGGER',
    'LOGF_STACK_INFO',
    'LOGF_LOG_EXCEPTION',
    'LOGF_SINGLE_EXCEPTION',
)


class Env:
    def __init__(self):
        for evar in EVARS:
            setattr(self, evar, os.environ.get(evar))


class Cfg:
    def __init__(self, **kwargs):
        self.level = kwargs.get('level')
        self.max_str = kwargs.get('max_str_len')
        self.log_time = kwargs.get('log_exec_time')
        self.single = kwargs.get('single_msg')
        self.log_ex = kwargs.get('log_exception')
        self.single_ex = kwargs.get('single_exception')
        self.log_stack = kwargs.get('log_stack_info')
        self.use_print = kwargs.get('use_print')
        self.log_args = kwargs.get('log_args')
        self.log_return = kwargs.get('log_return')
        self.use_logger = kwargs.get('use_logger')

        # Override attributes based on environment variables
        for ev in EVARS:
            _ev = os.environ.get(ev)
            if _ev is not None:
                if ev == 'LOGF_MAX_STR_LEN':
                    self.max_str = None if _ev.lower() == 'none' else int(_ev)
                elif ev == 'LOGF_SINGLE_MSG':
                    self.single = _ev.lower() == 'true'
                elif ev == 'LOGF_USE_PRINT':
                    self.use_print = _ev.lower() == 'true'
                elif ev == 'LOGF_LOG_ARGS':
                    self.log_args = _ev.lower() == 'true'
                elif ev == 'LOGF_LOG_RETURN':
                    self.log_return = _ev.lower() == 'true'
                elif ev == 'LOGF_LOG_EXEC_TIME':
                    self.log_time = _ev.lower() == 'true'
                elif ev == 'LOGF_USE_LOGGER':
                    self.use_logger = getLogger(_ev) if _ev else None
                elif ev == 'LOGF_STACK_INFO':
                    self.log_stack = _ev.lower() == 'true'
                elif ev == 'LOGF_LOG_EXCEPTION':
                    self.log_ex = _ev.lower() == 'true'
                elif ev == 'LOGF_SINGLE_EXCEPTION':
                    self.single_ex = _ev.lower() == 'true'


ARGSSTR = '{func_args} {func_kwargs}'
ENTER_MSG = '{func_name}() | {args_str}'
EXIT_MSG_NO_RETURN = '{func_name}() {exec_time}s'
EXIT_MSG = '{func_name}() {exec_time}s | {result}'
SINGLE_MSG = '{func_name}() {exec_time}s | {args_str} | {result}'
ENTER_MSG_NO_ARGS = '{func_name}()'

ERROR_MSG = 'ERROR {func_name}(): {exc_type} | {exc_val}'


class MSG_FORMATS:
    argstr = ARGSSTR
    enter = ENTER_MSG
    enter_no_args = ENTER_MSG_NO_ARGS
    exit = EXIT_MSG
    exit_no_return = EXIT_MSG_NO_RETURN
    single = SINGLE_MSG
    error = ERROR_MSG
