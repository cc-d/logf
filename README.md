# logf

the @logf() decorator i previously had as part of the myfuncs pip package, decided to make it standalone pip package this is the repo for it

## Usage

Here is a brief guide on how to use the `logfunc` module.

### Installation

First, you need to install the `logfunc` package. This can be done through pip:

```sh
pip install myfuncs
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
def my_function(a, b):
    return a + b
```

In the example above, `logf()` is used to wrap `my_function`. When `my_function` is called, it logs the function name, arguments, return value, and execution time.

### Customize Logging

The `logf` function allows you to customize your logging:

- You can set the log level with the `level` parameter.
- Use `log_args` and `log_return` parameters to choose whether to log the arguments and the return value of the function.
- `max_str_len` parameter allows you to set the maximum length of the logged arguments and return values.
- You can choose whether to measure and log the function execution time with the `measure_time` parameter.

Here is an example:

```python
from logfunc import logf

@logf(level='INFO', log_args=False, log_return=True, max_str_len=500, measure_time=True)
def my_function(a, b):
    return a + b
```

In this example, the function logs at the 'INFO' level, it doesn't log the function arguments, it logs the return value, trims logged strings to 500 characters, and it measures and logs the execution time.