from logfunc import logf
import os
import timeit
from functools import wraps


# Functions
def sm():
    return 2 + 2


def cm(n):
    return sum(i**2 for i in range(n))


def so():
    return "hello" * 100


def ls():
    return [x * 2 for x in range(500)]


def dc():
    return {x: x**2 for x in range(500)}


def rc():
    return [str(x) for x in range(300)]


def np(n):
    return n * 10


def sp(s):
    return s * 2


def sq(n):
    return n**2


def dv(n):
    return n / 2


funcs = [sm, cm, so, ls, dc, rc, np, sp, sq, dv]
logf_funcs = {}

from functools import partial


def wrapper(f, *args, **kwargs):
    @logf()
    def wrapped(*a, **k):
        return f(*a, **k)

    return wrapped(*args, **kwargs)


for f in funcs:
    logf_funcs[f] = partial(wrapper, f)


# Benchmark function
def b(f, *a, **k):
    return timeit.timeit(lambda: f(*a, **k), number=1000)


# Environment settings
e_vars = [
    {
        "LOGF_LEVEL": "DEBUG",
        "LOGF_MAX_STR_LEN": "10",
        "LOGF_SINGLE_MSG": "True",
        "LOGF_USE_PRINT": "True",
    }
]

# Test case setup
short_args = [
    ("sm", sm, logf_funcs[sm], [], {}),
    ("cm", cm, logf_funcs[cm], [100], {}),
    ("so", so, logf_funcs[so], [], {}),
    ("ls", ls, logf_funcs[ls], [], {}),
    ("dc", dc, logf_funcs[dc], [], {}),
    ("rc", rc, logf_funcs[rc], [], {}),
    ("np", np, logf_funcs[np], [1], {}),
    ("sp", sp, logf_funcs[sp], ["a"], {}),
    ("sq", sq, logf_funcs[sq], [2], {}),
    ("dv", dv, logf_funcs[dv], [4], {}),
]

# Use a lower range for cm_large to make the test 1/10 as long
extra_cases = [("cm_large", cm, logf_funcs[cm], [1000], {})]
cases = short_args + extra_cases * 19

cases.extend(extra_cases * 19)


def main():
    for e in e_vars:
        os.environ.update(e)
        r = []
        print(f"\nTesting with logf settings: {e}")

        for d, f, f_l, a, k in cases:
            nf, lf = b(f, *a, **k), b(f_l, *a, **k)
            df = abs(nf - lf)
            r.append((d, nf, lf, df))

        print("Summary:")
        print('-' * 50)
        for d, nf, lf, df in r:
            print(f"{d}: No logf: {nf:.8f} | Logf: {lf:.8f} | Diff: {df:.8f}")


if __name__ == "__main__":
    main()
