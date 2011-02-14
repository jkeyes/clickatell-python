import os
from setuptools import setup

def read(fname):
    """Utility function to read the README file.
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "clickatell",
    version = "0.5.0",
    author = "John Keyes",
    author_email = "johnkeyes@gmail.com",
    description = ("The clickatell module."),
    license = "Apache",
    keywords = "clickatell sms gateway",
    url = "http://keyes.ie/clickatell",
    packages=['clickatell'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
