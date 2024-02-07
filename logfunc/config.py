import os
from typing import Optional as Opt, Union


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
)


class Env:
    LOGF_LEVEL: str  # : Union[str, None]
    LOGF_USE_PRINT: str  # : Union[str, None]
    LOGF_SINGLE_MSG: str  # : Union[str, None]
    LOGF_MAX_STR_LEN: str  # : Union[str, None]
    LOGF_LOG_ARGS: str  # : Union[str, None]
    LOGF_LOG_RETUnionRN: str  # : Union[str, None]
    LOGF_LOG_EXEC_TIME: str  # : Union[str, None]
    LOGF_USE_LOGGER: str  # : Union[str, None]
    LOGF_STACK_INFO: str  # : Union[str, None]
    LOGF_LOG_EXCEPTION: str  # : Union[str, None]

    def __init__(self):
        for evar in EVARS:
            setattr(self, evar, os.environ.get(evar))


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
