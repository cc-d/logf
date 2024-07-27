import os
import random as ran
import string as s
from typing import Optional as Opt, Union as U, Any
from logging import getLogger

import random as ran
import string as s
from . import defaults as _def


ID_CHARS = s.ascii_letters + s.digits + '_-'
ID_LEN = 6

EVARS = (
    ('LOGF_IDENTIFIER', 'identifier', 'identifier', _def.IDENTIFIER),
    ('LOGF_LEVEL', 'level', 'level', _def.LEVEL),
    ('LOGF_LOG_ARGS', 'log_args', 'log_args', _def.LOG_ARGS),
    ('LOGF_LOG_RETURN', 'log_return', 'log_return', _def.LOG_RETURN),
    ('LOGF_STACK_INFO', 'log_stack', 'log_stack_info', _def.LOG_STACK_INFO),
    ('LOGF_LOG_EXEC_TIME', 'log_time', 'log_exec_time', _def.LOG_EXEC_TIME),
    (
        'LOGF_LOG_LEVEL',
        'logf_log_level',
        'logf_log_level',
        _def.LOGF_LOG_LEVEL,
    ),
    ('LOGF_MAX_STR_LEN', 'max_str', 'max_str_len', _def.MAX_STR_LEN),
    ('LOGF_SINGLE_MSG', 'single', 'single_msg', _def.SINGLE_MSG),
    ('LOGF_USE_LOGGER', 'use_logger', 'use_logger', _def.USE_LOGGER),
    ('LOGF_USE_PRINT', 'use_print', 'use_print', _def.USE_PRINT),
    ('LOGF_REFRESH', 'refresh', 'refresh', _def.REFRESH),
)


class Cfg:

    @classmethod
    def _eval_evar(cls, name: str, val: str, evdef: Any) -> Any:
        if isinstance(evdef, bool):
            return False if val.lower() == 'false' else True
        elif name == 'LOGF_USE_LOGGER':
            return getLogger(val) if val else None
        elif name == 'LOGF_MAX_STR_LEN':
            return None if val.lower() == 'none' else int(val)
        return val

    def _load_evars(self, **kwargs):
        for evtup in EVARS:
            evname, evattr, evkwarg, evdef = evtup
            val = os.environ.get(evname)

            if val is None:
                setattr(self, evattr, kwargs.get(evkwarg, evdef))
            else:
                setattr(self, evattr, self._eval_evar(evname, val, evdef))

    def __init__(self, **kwargs):
        # Override attributes based on environment variables
        self._kwargs = kwargs
        self._load_evars(**self._kwargs)

    def refresh(self):
        self._load_evars(**self._kwargs)

    def __repr__(self):  # pragma: no cover
        attrs = ', '.join(
            '%s=%r' % (k, v)
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        )
        return '<Cfg %s>' % attrs


ENTER_MSG = '->|{id_func_name} {args_str}'
EXIT_MSG_NO_RETURN = '{id_func_name} {exec_time}'
EXIT_MSG = '<-|{id_func_name} {exec_time} {result}'
SINGLE_MSG = '<>|{func_name} {exec_time} {args_str} | {result}'
ENTER_MSG_NO_ARGS = '->|{id_func_name}'


class MSG_FORMATS:

    enter = ENTER_MSG
    enter_no_args = ENTER_MSG_NO_ARGS
    exit = EXIT_MSG
    exit_no_return = EXIT_MSG_NO_RETURN
    single = SINGLE_MSG
