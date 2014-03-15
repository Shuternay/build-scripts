from distutils.core import setup

setup(
    name='build-scripts',
    version='1.0.1-r2',
    packages=['build_scripts'],
    package_data={'build_scripts': ['data/bootstrap/*', 'data/*.cpp', 'data/*.h']},
    url='https://github.com/Shuternay/build-scripts',
    license='',
    author='shuternay',
    author_email='shuternay@gmail.com',
    description='',
    scripts=['problem-control']
)
