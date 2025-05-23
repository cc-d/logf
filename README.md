# logfunc - @logf()

`@logf()` is a Python decorator designed for uncomplicated and immediate addition of logging to functions. Its main goal is to provide developers with a tool that can be added quickly to any function and left in place without further adjustments.

I originally made `@logf()` for my own use, but I hope it can be useful to others as well.

## Highlights

- **Async Support**: Incorporated from version 1.6 onwards.
- **Broad Python 3 Compatibility**: Designed to work seamlessly across multiple Python 3 versions,
- **Effortless Logging**: Implement logging without disrupting the flow of your code.
- **Leave-and-Forget**: Once integrated, no further adjustments are needed.
- **Encourages Logic Compartmentalization**.
- **Customizable**: Numerous settings available for tailoring logging behavior to specific needs.
- **Environment Variables**: Overriding default settings made easy with environment variables.
- **Log Exceptions**: Option to log exceptions before they are raised.

## Usage

### Installation

To integrate `@logf()` into your projects:

```sh
pip install logfunc
```

### Importing

Simply import the decorator to start using it:

```python
from logfunc import logf
```

### Basic Usage

Apply the `@logf()` decorator to functions you intend to log:

```python
from logfunc import logf

@logf()
def concatenate_strings(str1: str, str2: str) -> str:
    return str1 + str2
```

This setup ensures automatic logging of function name, parameters, return values, and execution time.

### @logf() args

- `level`: Set the log level (DEBUG, INFO, WARNING, etc.).
- `log_args` & `log_return`: Control whether to log arguments and return values.
- `max_str_len`: Limit the length of logged strings.
- `log_exec_time`: Option to log the execution time.
- `single_msg`: Consolidate all log data into a single message.
- `use_print`: Choose to `print()` log messages instead of using standard logging.
- `log_stack_info`: Pass `stack_info=$x` to `.log()` but not print
- `use_logger`: Pass a logger name or logger object to use instead of logging.log
- `identifier`: Add a unique identifier to enter/exit log messages.

**print_all** used to be an env var, now just unset LOGF_LEVEL and set USE_PRINT=True for the same effect.

### Environment Variable Overrides

Modify the behavior of `@logf()` using environment variables:

| Env Var            | Example Values       |
| ------------------ | -------------------- |
| LOGF_LEVEL         | DEBUG, INFO, WARNING |
| LOGF_MAX_STR_LEN   | 10, 50, 10000000     |
| LOGF_SINGLE_MSG    | True, False          |
| LOGF_USE_PRINT     | True, False          |
| LOGF_STACK_INFO    | True, False          |
| LOGF_LOG_EXEC_TIME | True, False          |
| LOGF_LOG_ARGS      | True, False          |
| LOGF_LOG_RETURN    | True, False          |
| LOGF_USE_LOGGER    | 'logger_name'        |
| LOGF_LOG_LEVEL     | DEBUG, INFO, WARNING |
| LOGF_IDENTIFIER    | True, False          |

See the following output for an example of how an env var will affect `@logf()` behaviour:

With `LOGF_USE_PRINT=True`:

```
> con_time() (<function rec_self_func at 0x104f3a980>)
> rec_self_func() 
> rec_self_func() (<function rec_self_func at 0x104f3a980>, 1, 5)
< rec_self_func() 8.11us <function rec_self_func at 0x104f3a980>
< rec_self_func() 55.07us <function rec_self_func at 0x104f3a980>
< con_time() 0.454ms <__main__.con_time object at 0x105bc9d30>
> con_time() (<function rec_self_func at 0x104f3a980>, False)
> rec_self_func() (False)
> rec_self_func() (False, 1, 5)
< rec_self_func() 5.96us False
< con_time() 0.106ms <__main__.con_time object at 0x105be4690>

> wrap() 
> asynctest() 
< asynctest() 60.25us 1
< wrap() 4.232ms 1
```

With `LOGF_SINGLE_MSG=True`:

```
- rec_self_func() 1.91us (<function rec_self_func at 0x1044c2980>, 5, 5) | <function rec_self_func at 0x1044c2980>
- rec_self_func() 72.00us (<function rec_self_func at 0x1044c2980>, 4, 5) | <function rec_self_func at 0x1044c2980>
- rec_self_func() 88.21us (<function rec_self_func at 0x1044c2980>, 3, 5) | <function rec_self_func at 0x1044c2980>
- rec_self_func() 97.99us (<function rec_self_func at 0x1044c2980>, 2, 5) | <function rec_self_func at 0x1044c2980>
- rec_self_func() 0.110ms (<function rec_self_func at 0x1044c2980>, 1, 5) | <function rec_self_func at 0x1044c2980>
- rec_self_func() 0.118ms  | <function rec_self_func at 0x1044c2980>
- con_time() 0.143ms (<function rec_self_func at 0x1044c2980>) | <__main__.con_time object at 0x104b61d30>
- rec_self_func() 1.91us (False, 5, 5) | False
- rec_self_func() 10.01us (False, 4, 5) | False
- rec_self_func() 17.17us (False, 3, 5) | False
- rec_self_func() 21.93us (False, 2, 5) | False
- rec_self_func() 27.89us (False, 1, 5) | False
- rec_self_func() 34.09us (False) | False
```

With `LOGF_IDENTIFIER=True`:

```
> [6s_fGj] rec_self_func() (False)
> [gn2LsO] rec_self_func() (False, 1, 2)
> [-vzlsf] rec_self_func() (False, 2, 2)
< [-vzlsf] rec_self_func() 5.96us False
< [gn2LsO] rec_self_func() 26.94us False
< [6s_fGj] rec_self_func() 46.25us False
```

### Real-world Examples

Here are a couple of real-world examples of `@logf()` usage:

```python
from logfunc import logf


# Database operations
@logf(level='ERROR')
def db_insert(item):
    # Insert item into database
    pass

# Asynchronous tasks in an application
@logf()
async def fetch_data(url):
    # Fetch data from URL asynchronously
    return data
```

## Testing

Activate/create your venv with `python3 -m venv venv` and `source venv/bin/activate` if you haven't already.

Run `pip install -r requirements_dev.txt` to install the testing dependencies.

Run `pytest tests.py` to run the tests.

Output should look like this:

```sh
coverage: platform darwin, python 3.13.2-final-0

Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
logfunc/__init__.py       2      0   100%
logfunc/config.py        53      0   100%
logfunc/defaults.py      14      0   100%
logfunc/main.py          73      0   100%
logfunc/msgs.py          10      0   100%
logfunc/utils.py         57      0   100%
logfunc/version.py        1      0   100%
---------------------------------------------------
TOTAL                   210      0   100%

40 passed, 3 warnings in 0.15s 
25 passed in 0.06s
```

You can also just run the `tests.py` file directly.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

MIT

## Contact

ccarterdev@gmail.com
