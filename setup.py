import os
try :
    from setuptools import setup
except ImportError :
    from distutils.core import setup
    
readme = open(os.path.join(os.path.dirname(__file__), 'README'), 'r').read()

setup(
    name='ACIS-pandas',
    author='Bill Noon',
    author_email='wn10@cornell.edu',
    version='0.1.0',
    url='http://github.com/bnoon/acis-pandas',
    py_modules=['ACISLoader'],
    description='Access the ACIS data via a pandas Panel.',
    long_description=readme,
    zip_safe=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python'
    ]
)
