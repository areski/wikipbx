import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='WikiPBX',
    version='%i.%i.%i-%s-%i' % __import__('wikipbx').VERSION,
    author='Traun Leyden',
    author_email='tleyden@branchcut.com',
    description='Open Source Web GUI front-end for Freeswitch',
    url='http://www.wikipbx.org',
    packages=['wikipbx'],
    license='MIT',
    long_description=read('README'),
    classifiers=[
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
)

