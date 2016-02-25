# coding: utf-8
#

import sys
sys.path.insert(0,'/usr/lib/pyshared/python2.7')

from setuptools import setup, find_packages

from airtest import __version__

long_description = ''
try:
    with open('README.md') as f:
        long_description = f.read()
except:
    pass

setup(
      name='airtest',
      version=__version__,
      description='mobile test(black air) python lib',
      long_description=long_description,

      author='codeskyblue',
      author_email='codeskyblue@gmail.com',

      packages = find_packages(),
      include_package_data=True,
      package_data={},
      install_requires=[
          #'Appium-Python-Client >= 0.10',
          'click >= 3.3',
          'fuckit >= 4.8.0',
          'humanize >= 0.5',
          'pystache >= 0.5.4',
          'aircv >= 1.02',
          'Flask >= 0.10.1',
          # 'paramiko',
          #'androidviewclient >= 7.1.1', 
          # 'requests >= 2.4.3', 
          ],
      entry_points='''
      [console_scripts]
      air.test = airtest.console:main
      ''')
