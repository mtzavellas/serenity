from glob import glob
from os.path import splitext, basename

import setuptools

with open('README.rst', 'r') as fh:
    readme = fh.read()

with open('HISTORY.rst', 'r') as f:
    history = f.read()


requires = [
    'coinbasepro',
    'fire',
    'gemini-python',
    'numpy',
    'pandas',
    'phemex',
    'psycopg2',
    'pytau',
    'python-binance',
    'pytz',
    'scipy',
    'tables',
    'websockets',
    'yfinance'
]

setuptools.setup(
    name='serenity-trading',
    version='0.2.0',
    description='A Python cryptocurrency trading system.',
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    license='MIT',
    author='Kyle F. Downey',
    author_email='kyle.downey@gmail.com',
    url='https://github.com/cloudwall/serenity',
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    python_requires='>=3.7.x',
    install_requires=requires,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ),
)
