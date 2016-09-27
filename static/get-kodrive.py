#!/usr/bin/env python
import os
import sys
from subprocess import call
import shutil
import platform

try:
    WindowsError
except NameError:
    IS_WIN = False
    PIP = '/bin/pip'
    KODRIVE = '/bin/kodrive'
else:
    IS_WIN = True
    PIP = '/Scripts/pip.exe'
    KODRIVE = '/Scripts/kodrive.exe'

DEFAULT_KODRIVE_HOME = os.path.expanduser('~/.local/venvs')
DEFAULT_KODRIVE_BIN_DIR = os.path.expanduser('~/.local/bin')
virtualenv_bin = 'virtualenv'
pip_bin = 'pip'

def echo(msg=''):
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()


def fail(msg):
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()
    sys.exit(1)


def succeed(msg):
    echo(msg)
    sys.exit(0)


def command_exists(cmd):
    with open(os.devnull, 'w') as null:
        try:
            return call(
                [cmd, '--version'],
                stdout=null, stderr=null) == 0
        except OSError:
            return False


def publish_script(venv, bin_dir):

    echo('Installing kodrive binary to ' + bin_dir)
    if IS_WIN:
        for name in os.listdir(venv + '/Scripts'):
            if 'kodrive' in name.lower():
                shutil.copy(venv + '/Scripts/' + name, bin_dir)
    else:
        os.symlink(venv + '/bin/kodrive', bin_dir + '/kodrive')

def install_files(venv, bin_dir, install):
    try:
        os.makedirs(bin_dir)
    except OSError:
        pass

    def _cleanup():
        try:
            shutil.rmtree(venv)
        except (OSError, IOError):
            pass

    global virtualenv_bin
    if call([virtualenv_bin, venv]) != 0:
        _cleanup()
        fail('Could not create virtualenv for kodrive :(')

    if call([venv + PIP, 'install', install]) != 0:
        _cleanup()
        fail('Could not install kodrive :(')

    publish_script(venv, bin_dir)


def main():
    if command_exists('kodrive'):
        succeed('You already have kodrive installed')
    else:
        echo('Installing kodrive...')

    global virtualenv_bin
    system = platform.system()

    if system == "Linux":
        if not command_exists(virtualenv_bin):
            if not command_exists(pip_bin): 
                echo('You need to have pip installed to bootstrap kodrive.')
                fail('Please run, curl https://bootstrap.pypa.io/get-pip.py | sudo python, to install pip.')

            virtualenv_bin = "%s/.local/bin/virtualenv" % os.path.expanduser("~")
            if not command_exists(virtualenv_bin):
                echo('You need to have virtualenv installed to bootstrap kodrive.')
                fail('Please run, pip install --user virtualenv, to install virtualenv.')

    elif system == "Darwin":
        if not command_exists(virtualenv_bin):
            if not command_exists(pip_bin): 
                echo('You need to have pip installed to bootstrap kodrive.')
                fail('Please run, curl https://bootstrap.pypa.io/get-pip.py | sudo python, to install pip.')

            virtualenv_bin = "%s/Library/Python/2.7/bin/virtualenv" % os.path.expanduser("~")
            if not command_exists(virtualenv_bin):
                echo('You need to have virtualenv installed to bootstrap kodrive.')
                fail('Please run, pip install --user virtualenv, to install virtualenv.')


    elif system == "Windows":
        fail('kodrive is not supported on Windows.')

    else:
        fail("kodrive is not supported on %s." % system)


    bin_dir = os.environ.get('KODRIVE_BIN_DIR', DEFAULT_KODRIVE_BIN_DIR)
    venv = os.path.join(os.environ.get('KODRIVE_HOME', DEFAULT_KODRIVE_HOME),
                        'kodrive')
    install_files(venv, bin_dir, 'kodrive')
    # Start kodrive 
    call([os.path.join(DEFAULT_KODRIVE_BIN_DIR, 'kodrive'), 'sys', 'start'])

    # Set PATH variable
    if  'SHELL' in os.environ:
        if 'bash' in os.environ['SHELL']:
            bashrc = os.path.expanduser("~/.bashrc")
            with open(bashrc, 'a+') as f:
                f.write('export PATH="$HOME/.local/bin:$PATH"')

            if not command_exists('kodrive') != 0:
                echo()
                echo('=' * 60)
                echo()
                echo('WARNING:')
                echo('  It looks like {0} is not in your PATH so kodrive will'.format(bin_dir))
                echo('  not work out of the box. To fix this problem make sure to run')
                echo('  one of the following depending on which shell you are using.')
                echo()
                echo('  bash: export PATH={0}:$PATH'.format(bin_dir))
                echo()
                echo('=' * 60)
                echo()

        elif 'csh' in os.environ['SHELL']:
            cshrc = os.path.expanduser("~/.cshrc")
            with open(cshrc, 'a+') as f:
                f.write('set path=($home/.local/bin $path)')

            if not command_exists('kodrive') != 0:
                echo()
                echo('=' * 60)
                echo()
                echo('WARNING:')
                echo('  It looks like {0} is not in your PATH so kodrive will'.format(bin_dir))
                echo('  not work out of the box. To fix this problem make sure to run')
                echo('  one of the following depending on which shell you are using.')
                echo()
                echo("  tcsh: set path=(%s $path)" % bin_dir)
                echo()
                echo('=' * 60)
                echo()
    
    succeed('kodrive is now installed.')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # we are being tested
        install_files(*sys.argv[1:])
    else:
        main()
