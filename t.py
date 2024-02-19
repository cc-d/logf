from logfunc.main import logf
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


run_in_thread(4)
