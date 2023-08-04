# logf

`@logf()` is a decorator designed to enable effortless logging of your Python functions' execution, requiring zero configuration for basic usage. Formerly a part of the myfuncs pip package, it is now a standalone pip package. This repository is dedicated to its continued development and maintenance.

## Usage

This is a brief guide on how to use the `logfunc` module.

### Installation

Firstly, you need to install the `logfunc` package. This can be done through pip:

```sh
pip install logfunc
```

### Importing

Once the package is installed, you can import the `logf` function from the `logfunc` module:

```python
from logfunc import logf
```

### Logging Function Execution

The `logf` function is a decorator that you can apply to any function you want to log:

```python
from logfunc import logf

@logf()
def my_function(a, b='b'):
    return str(a) + str(b) + 'c'
```

In the example above, `logf()` is used to wrap `my_function`. When `my_function` is called, it logs the function name, arguments, return value, and execution time.

```
>>> my_function('a')
my_function() | ('a',) {}
my_function() 0.00051s | abc
'abc'
```

### Customize Logging

The `logf` decorator allows you to customize your logging:

- You can set the log level with the `level` parameter.
- Use `log_args` and `log_return` parameters to choose whether to log the arguments and the return value of the function.
- `max_str_len` parameter allows you to set the maximum length of the logged arguments and return values. If `None` is passed, the entire args/kwargs/result are logged as their full-length strings.
- You can choose whether to measure and log the function execution time with the `log_exec_time` parameter.
- You can include the execution time, args, and return value in a single message with the `single_msg` parameter.
- `use_print` print() log messages rather than logging them

Here is an example:

```python
from logfunc import logf

@logf(level='INFO', log_args=False, log_return=True,
    max_str_len=None, log_exec_time=True, single_msg=True)
def my_function(a, b):
    return a + b
```

In this example, the function logs at the 'INFO' level, it doesn't log the function arguments, it logs the return value, logs the entire return string without any truncation, and it measures and logs the execution time, and it only uses a single log message as opposed to two on enter/exit.

### Environment Variables

The `logf` function supports overriding some default/passed parameters with environment variables:

| Env Var          | Example Values       |
|------------------|-------------|
| LOGF_LEVEL       | DEBUG INFO WARNING ERROR CRITICAL 10 20 30 40 50|
| LOGF_MAX_STR_LEN | 10 50 10000000 None NONE none |
| LOGF_SINGLE_MSG  | True False
| LOGF_USE_PRINT   | True False


## Testing

This module comes with a test suite which you can run to ensure that `logf` behaves as expected. The tests are implemented using Python's built-in `unittest` module.

To run the tests, navigate to the directory where the `logfunc` package is installed and run:

```sh
python tests.py
```

The test suite includes tests for the default behavior of the `logf` decorator as well as its behavior when custom parameters are passed. The tests check whether the function name, arguments, return value, and execution time are correctly logged, and whether the `max_str_len` parameter correctly truncates the logged strings.
