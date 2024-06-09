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
