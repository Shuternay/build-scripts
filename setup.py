#from distutils.core import setup
from setuptools import setup

setup(
    name='olymper',
    version='1.0.5',
    packages=['olymper'],
    package_data={'olymper': ['data/bootstrap/*', 'data/*.cpp', 'data/*.h']},
    url='https://github.com/Shuternay/build-scripts',
    license='',
    author='shuternay',
    author_email='shuternay@gmail.com',
    description='',
    entry_points={
        'console_scripts': [
            'olymper = olymper.problem_control:main',
            'process-runlog = olymper.process_run_log:main',
        ],
    },
    install_requires=[
        'jsoncomment', 'paramiko', 'scp'
    ],
)
