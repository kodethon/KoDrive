import pytest

from click.testing import CliRunner
from kodrive import cli
from kodrive import syncthing_factory as factory
from kodrive.data import autostart as aust

import time, os, json 
import shutil, subprocess, platform

from mock import cli as mock


# NOTE: Only tests Mac OSX for now,
# refactor when Linux autostart written

@pytest.fixture
def runner():
  return CliRunner()

def test_autostart(runner):
  ''' Ensures that kodrive will autostart  '''

  system = platform.system()
  result = runner.invoke(cli.sys, ['start'])
  mock.client.wait_start(0.5, 10)

  if system == "Linux":
    home = os.path.expanduser('~')
    dirpath = os.path.join(home, '.config', 'systemd', 'user')
    service_name = 'syncthing.service'
    st_service_path = os.path.join(dirpath, service_name)
    
    # Ensure that file exists
    if not os.path.exists(st_service_path):
      assert False
    
    # Ensure that data was correctly written
    fp = open(st_service_path)
    data = fp.read()
    fp.close

    assert data == aust.getSyncthingService()

  elif system == "Darwin":

    if result.exception:
      print result.exception
      assert False

    if not mock.client.ping():
      assert False

    kodrive_config = mock.client.adapter.get_config()
    plist_name = 'com.kodrive.autostart'

    daemon_list = subprocess.check_output([
      'launchctl', 'list'   
    ], stderr=subprocess.STDOUT)

    if plist_name not in daemon_list:
      print daemon_list
      print '--------------------end of daemon list---------------------'
      print 'kodrive was not added to the autostart list'
      assert False

    result = runner.invoke(cli.sys, ['stop'])

    if result.exception:
      print result.exception
      assert False

    if mock.client.ping():
      result = runner.invoke(cli.sys, ['stop'])

      if result.exception:
        print result.exception
        assert False
  
      if mock.client.ping():
        assert False

