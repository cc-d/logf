#!/bin/sh

pytest -n 4 -vv -q -s --show-capture=all --cov=./logfunc --cov-report=term-missing --color=yes -W ignore::DeprecationWarning tests.py
