
from setuptools import setup, find_packages



setup(
    name='logfunc',
    version='1.0.2',
    packages=find_packages(),
    install_requires=[],
    author='Cary Carter',
    author_email='ccarterdev@gmail.com',
    description='A function decorator/wrapper which allows for logging of args, kwargs, execution time, return value, etc of a func',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/cc-d/myfuncs',
    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

