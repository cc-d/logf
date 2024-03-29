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
- `use_logger`: Pass a logger name or logger object to use instead of logging.lo
- `log_exception`: Log exceptions if they occur before they are raised.
- `single_exception`: Consolidate all exception log data into a single message (intended to be used with `log_exception`).

**print_all** used to be an env var, now just unset LOGF_LEVEL and set USE_PRINT=True for the same effect.

### Environment Variable Overrides

Modify the behavior of `@logf()` using environment variables:

| Env Var               | Example Values       |
| --------------------- | -------------------- |
| LOGF_LEVEL            | DEBUG, INFO, WARNING |
| LOGF_MAX_STR_LEN      | 10, 50, 10000000     |
| LOGF_SINGLE_MSG       | True, False          |
| LOGF_USE_PRINT        | True, False          |
| LOGF_STACK_INFO       | True, False          |
| LOGF_LOG_EXEC_TIME    | True, False          |
| LOGF_LOG_ARGS         | True, False          |
| LOGF_LOG_RETURN       | True, False          |
| LOGF_LOG_EXCEPTION    | True, False          |
| LOGF_USE_LOGGER       | 'logger_name'        |
| LOGF_SINGLE_EXCEPTION | True, False          |
| LOGF_LOG_LEVEL        | DEBUG, INFO, WARNING |

See the following output for an example of how an env var will affect `@logf()` behaviour:

Without `LOGF_USE_PRINT`:

```
mym2@Carys-MacBook-Pro liberfy-cli % ./cli user me
Namespace(cmd='user', act='me')
email='a@a.a' id='a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'
```

With `LOGF_USE_PRINT=True`: (jwt here isnt sensitive so no worries)

```
mym2@Carys-MacBook-Pro liberfy-cli % LOGF_USE_PRINT=True ./cli user me
async_main | () {}
setup_argparse | () {}
setup_argparse() 0.00144s | ArgumentParser(prog='main.py', usage=None, description='CLI for user, project, sync directory, and directory file management.', formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True)
apicmd | (ArgumentParser(prog='main.py', usage=None, description='CLI for user, project, sync directory, and directory file management.', formatter_class=<class 'argparse.HelpFormatter'>, conflict_handler='error', add_help=True),) {}
Namespace(cmd='user', act='me')
me | () {}
get | ('/u/me',) {}
_method | ('get', '/u/me') {}
_inject_auth | ({},) {}
load_token | () {}
load_token() 0.00004s | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQ1NTQ1MjAsInN1YiI6ImFAYS5hIiwiaWF0IjoxNjk0NTQ3MzIwfQ.p6NPOEAedaV6SzBkv3XYWTGmZ4sdAEshk76wacV6Jlw
_inject_auth() 0.00005s | {'headers': {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQ1NTQ1MjAsInN1YiI6ImFAYS5hIiwiaWF0IjoxNjk0NTQ3MzIwfQ.p6NPOEAedaV6SzBkv3XYWTGmZ4sdAEshk76wacV6Jlw'}}
resp_exceptions | (<Response [200 OK]>,) {}
resp_exceptions() 0.00002s | None
_method() 0.01756s | {'email': 'a@a.a', 'id': 'a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'}
get() 0.01757s | {'email': 'a@a.a', 'id': 'a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'}
me() 0.01760s | email='a@a.a' id='a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'
apicmd() 0.01773s | email='a@a.a' id='a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'
email='a@a.a' id='a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'
async_main() 0.01922s | email='a@a.a' id='a4c3f7ac-4649-4e74-ad07-1cd8e9626bbc'
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
---------- coverage: platform darwin, python 3.11.5-final-0 ----------
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
logfunc/__init__.py       1      0   100%
logfunc/config.py        22      0   100%
logfunc/defaults.py       1      0   100%
logfunc/main.py         107      0   100%
logfunc/utils.py         28      0   100%
tests.py                282      0   100%
---------------------------------------------------
TOTAL                   441      0   100%

```

You can also just run the `tests.py` file directly.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

MIT

## Contact

ccarterdev@gmail.com
