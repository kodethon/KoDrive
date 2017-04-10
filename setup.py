"""
Synchronize remote files with local directory.
"""
from setuptools import find_packages, setup
import sys, os

# Deprecated, may be needed for packaging later though
def get_data_files():
    """ Return data_files in a platform dependent manner """

    if sys.platform.startswith('linux'):
        st_version = '0.14.3'
        linux_64_bit_dir = "syncthing-linux-amd64-v%s" % st_version
        bin_src = os.path.join('static/linux', linux_64_bit_dir, 'syncthing')
        license_src = os.path.join('static/linux', linux_64_bit_dir, 'LICENSE.txt')
        authors_src = os.path.join('static/linux', linux_64_bit_dir, 'AUTHORS.txt')
        dest = os.path.expanduser(os.path.join('~', '.st', linux_64_bit_dir))
        
        if not os.path.exists(dest):
            os.makedirs(dest)

        return [
            (dest, [bin_src]),
            (dest, [license_src]),
            (dest, [authors_src])
        ]
    elif os.name == 'nt':
        data_files = []
    else:
        data_files = []

    return data_files


dependencies = ['click', 'requests']

setup(
    name='kodrive',
    version='1.0.15',
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
            'kodrive = kodrive.cli:main',
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


