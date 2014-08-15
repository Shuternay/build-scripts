#from distutils.core import setup
from setuptools import setup

setup(
    name='build-scripts',
    version='1.0.5',
    packages=['build_scripts'],
    package_data={'build_scripts': ['data/bootstrap/*', 'data/*.cpp', 'data/*.h']},
    url='https://github.com/Shuternay/build-scripts',
    license='',
    author='shuternay',
    author_email='shuternay@gmail.com',
    description='',
    entry_points={
        'console_scripts': [
            'problem-control = build_scripts.problem_control:main',
            'process-runlog = build_scripts.process_run_log:main',
        ],
    }
)
