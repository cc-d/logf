from logfunc.main import logf
import asyncio
from time import sleep


@logf(log_exception=False, single_exception=False)
def f1(a):

    @logf()
    def f2(a):
        @logf(log_exception=False, single_exception=False)
        def f3(a):
            @logf(log_exception=False, single_exception=False)
            def f4(a):
                if a == 4:
                    raise ValueError("a is 4")
                return a

            f4(a)

        f3(a)

    f2(a)


import threading


def run_in_thread(a):
    from random import randint

    try:
        f1(4)
    except Exception as e:
        pass


# run_in_thread(4)

import os


decorator_configs = [
    {},
    {'level': 'info', 'log_args': False},
    {'log_return': False, 'single_msg': True},
    {'use_print': True, 'log_exception': False},
    {'single_exception': False, 'use_logger': 'logname'},
    {'level': 'debug', 'log_args': False, 'log_return': False},
    {'single_msg': True, 'use_print': True, 'log_exception': False},
    {
        'log_exception': True,
        'single_exception': False,
        'use_logger': 'logname',
        'level': 'info',
    },
    # Add more combinations as needed
]


def test_function():
    print("Test function executed")


import logging

logging.basicConfig(level=logging.DEBUG)


# Apply each configuration to the test function and execute it
for config in decorator_configs:
    decorated_test_function = logf(**config)(test_function)
    print(f"Testing configuration: {config}")
    decorated_test_function()
    print("-" * 50)
