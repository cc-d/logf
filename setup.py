from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='logfunc',
    version='1.9.1',
    packages=find_packages(),
    install_requires=[],
    author='Cary Carter',
    author_email='ccarterdev@gmail.com',
    description=(
        'An EASY TO USE function decorator for advanced logging of function'
        ' execution, including arguments, return values, and execution time.'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cc-d/logf/',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
