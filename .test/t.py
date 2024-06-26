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

        def f5(a):

            f3(a)

        f5(a)

    f2(a)


def decorator(func):
    def wrapper(*args, **kwargs):
        print('in wrapper of decorator')
        return func(*args, **kwargs)

    return wrapper


@decorator
def f0():
    f1(4)


try:
    f0()
except Exception as e:
    pass
import threading


def run_in_thread(a):
    from random import randint

    try:
        f1(4)
    except Exception as e:
        pass


def errs():
    @logf(use_print=True, log_exception=True)
    def f1():
        @logf(use_print=False, log_exception=True)
        def f3():
            raise Exception("f3 error")

        f3()

    @logf(use_print=False, log_exception=True)
    def f2():
        @logf(use_print=False, log_exception=True)
        def f3():
            raise Exception("f3 error")

        f3()

    try:
        print('try f1')
        f1()
        print('end f1')
    except Exception as e:
        print('except f1')
        pass

    try:
        print('try f2')
        f2()
        print('end f2')
    except Exception as e:
        print('except f2')
        pass


@logf()
def f1(a):

    @logf()
    def f2(a):
        @logf()
        def f3(a):
            @logf()
            def f4(a):
                if a == 4:
                    raise ValueError("a is 4")
                return a

            try:
                f4(a)
            except:
                raise BaseException("f4 error")

        @logf()
        def f5(a):
            raise Exception("Test exception")

        try:
            f3(a)
        except Exception as e:
            f5(a)

    f2(a)


f1('hi')
