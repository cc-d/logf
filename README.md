# logfunc - @logf()

### CURRENT VERSION: v1.7.0 | Last Change: Fixed Async exec time calc bug

`@logf()` is a Python decorator designed for uncomplicated and immediate addition of logging to functions. Its main goal is to provide developers with a tool that can be added quickly to any function and left in place without further adjustments.

I originally made `@logf()` for my own use, but I hope it can be useful to others as well.

## Highlights
- **Async Support**: Incorporated from version 1.6 onwards.
- **Broad Python 3 Compatibility**: Designed to work seamlessly across multiple Python 3 versions.
- **Effortless Logging**: Implement logging without disrupting the flow of your code.
- **Leave-and-Forget**: Once integrated, no further adjustments are needed.
- **Encourages Logic Compartmentalization**.
- **Customizable**: Numerous settings available for tailoring logging behavior to specific needs.
- **Environment Variables**: Overriding default settings made easy with environment variables.


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

### Environment Variables

Modify the behavior of `@logf()` using environment variables:

| Env Var          | Example Values       |
|------------------|----------------------|
| LOGF_LEVEL       | DEBUG, INFO, WARNING |
| LOGF_MAX_STR_LEN | 10, 50, 10000000     |
| LOGF_SINGLE_MSG  | True, False          |
| LOGF_USE_PRINT   | True, False          |

### Real-world Examples

To demonstrate its practicality, here are a few scenarios where `@logf()` can be beneficial:

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

To ensure reliability, `@logf()` comes equipped with a test suite. To run the tests:

```sh
python tests.py
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

MIT

## Contact

ccarterdev@gmail.com