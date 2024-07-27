## 2.9.1

individual arg/kwarg length plus udpated tests to confirm

exec time rounded to 0 executions now show exec time as 0.0s

updated tests

im tired

## 2.9.0

Added class names to **init** methods
might expand later

Improved identifier system

improved visual clarity on enter/exit

Made more efficient use of space, removed use of () in fucn names

## 2.8.0

added refresh_vars method to Cfg vlass allowing for re-evaluation of env vars
every time the logf wrapped function is called

added LOGF_REFRESH env var to control this behaviour

added tests/docs for this new functionality

## 2.7.1

removed usage of fstrings causing 3.5 tests to fail (showing why those are useful!!!!)

## 2.7.0

improved configuration object env var evaluation and defaults

changed all but the single msg format to not have |

added expected attr names, defaults, etc to cfg object

added more tests to ensure evar defaults and evaluation work correctly

## 2.6.2

Fixed incorrect metadata resulting from setup.py being used in build rathrer than pyproject.toml

## 2.6.0

added identifier plus LOGF_IDENTIFIER env var

updated README

added <- and -> to enter/exit log messages

test coverage back to 100%

## 2.5.1

moved from setup.py -> pyproject.toml

added version + set version script

fixed 3.5 python test.py support

## 2.5

added changelog

REMOVED ALL CUSTOM EXCEPTION BEHAVIOUR/HANDLING FOR COMPLEXITY REASONS

removed log_exception from env vars/docs/args/tests/etc
