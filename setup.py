"""
Synchronize remote files with local directory.
"""
from setuptools import find_packages, setup
import sys, os

def get_data_files():
    """ Return data_files in a platform dependent manner """

    if sys.platform.startswith('linux'):
        return [
            ('/etc/init.d', ['static/linux/kdr'])
        ]
    elif os.name == 'nt':
        data_files = []
    else:
        data_files = []

    return data_files


dependencies = ['click', 'requests']

setup(
    name='kdr',
    version='0.9.5',
    url='https://github.com/Jvlythical/KodeDrive',
    license='LICENSE',
    author='Michael Yen',
    author_email='lvlichael8@Gmail.Com',
    description='Synchronize remote files with local directory.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'kdr = kdr.cli:main',
        ],
    },
    #data_files=get_data_files(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        #'Development Status :: 1 - Planning',
        #'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        #'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)


