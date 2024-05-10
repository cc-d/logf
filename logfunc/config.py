import os
import random as ran
import string as s
from typing import Optional as Opt, Union
from logging import getLogger

import random as ran
import string as s


ID_CHARS = s.ascii_letters + s.digits + '_-'
ID_LEN = 6  # 68719476736 possible combinations

EVARS = (
    'LOGF_USE_PRINT',
    'LOGF_SINGLE_MSG',
    'LOGF_MAX_STR_LEN',
    'LOGF_LEVEL',
    'LOGF_LOG_ARGS',
    'LOGF_LOG_RETURN',
    'LOGF_LOG_EXEC_TIME',
    'LOGF_USE_LOGGER',
    'LOGF_LOG_LEVEL',
    'LOGF_STACK_INFO',
)


class Cfg:
    def __init__(self, **kwargs):
        self.level = kwargs.get('level')
        self.max_str = kwargs.get('max_str_len')
        self.log_time = kwargs.get('log_exec_time')
        self.single = kwargs.get('single_msg')
        self.use_print = kwargs.get('use_print')
        self.log_args = kwargs.get('log_args')
        self.log_return = kwargs.get('log_return')
        self.use_logger = kwargs.get('use_logger')
        self.logf_log_level = kwargs.get('logf_log_level')
        self.log_stack = kwargs.get('log_stack_info')

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
                elif ev == 'LOGF_SINGLE_EXCEPTION':
                    self.single_ex = _ev.lower() == 'true'
                elif ev == 'LOGF_LOG_LEVEL':
                    self.logf_log_level = str(_ev).upper()


ARGSSTR = '{func_args} {func_kwargs}'
ENTER_MSG = '{func_name}() | {args_str}'
EXIT_MSG_NO_RETURN = '{func_name}() {exec_time}s'
EXIT_MSG = '{func_name}() {exec_time}s | {result}'
SINGLE_MSG = '{func_name}() {exec_time}s | {args_str} | {result}'
ENTER_MSG_NO_ARGS = '{func_name}()'


class MSG_FORMATS:
    argstr = ARGSSTR
    enter = ENTER_MSG
    enter_no_args = ENTER_MSG_NO_ARGS
    exit = EXIT_MSG
    exit_no_return = EXIT_MSG_NO_RETURN
    single = SINGLE_MSG
