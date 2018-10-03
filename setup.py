from setuptools import setup, find_packages

with open('requirements.txt') as fp:
    INSTALL_REQUIRES = fp.read()

LONG_DESC = '''\
=====================================
Koo Client and Development Platform
=====================================
Koo is a Qt/KDE based client for Open ERP, a complete ERP and CRM. Koo
aims for great flexibility allowing easy creation of plugins and views, high
integration with KDE5 under Unix, Windows and Mac, as well as providing
a development platform for new applications using the Open ERP server.
A set of server side modules is also provided among the Koo distribution
which provide better attachments handling and full text search capabilities.
'''

CLASSIFIERS = """\
Development Status :: 5 - Production/Stable
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
Topic :: Desktop Environment :: K Desktop Environment (KDE)
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: MacOS
Topic :: Office/Business
"""


setup(
    name='koo',
    version='6.0.1',
    packages=find_packages(),
    url='http://www.NaN-tic.com/koo-platform',
    license='GPL',
    author='NaN',
    author_email='info@nan-tic.com',
    mantainer='GISCE-TI, S.L.',
    mantainer_email='devel@gisce.net',
    install_requires=INSTALL_REQUIRES,
    description='Koo Client',
    LONG_DESCription=LONG_DESC,
    CLASSIFIERS=[_f for _f in CLASSIFIERS.splitlines() if _f],
    include_package_data=True,
)

