# KodeDrive

Synchronize remote files with local directory.


# Installation

If you don't have `pipsi` installed, you can find 
the instructions to install it [here](https://github.com/mitsuhiko/pipsi#readme).

Otherwise, simply run:

    $ pipsi install .

Note: `pipsi` depends on [pip](https://github.com/pypa/pip) and [virtualenv](https://github.com/pypa/virtualenv) which may need to be installed.


# Getting Started

To use it:

    $ kdr --help

### Initializing a repository

### Synchronizing files and directories

### Conflicts

If a file is modified on different devices simultaneously, the file on the device with the larger value of the first 63 bits for their device ID will be marked as the conflicting file. The file will be renamed to '<filename>.sync- conflict-<date>-<time>.<ext>'

It will be up to the users to resolve conflicts and update their files in this case.

Please note that if users modify conflict files, it is possible to end up with conflicting conflict files.
Those will be named as 'sync-conflict-...sync-conflict -...-sync-conflict' files.