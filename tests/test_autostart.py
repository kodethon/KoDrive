import pytest

from click.testing import CliRunner
from kodrive import cli
from kodrive import syncthing_factory as factory

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

  if system == "Linux":
    print 'Linux does not autostart yet.'
    assert True

  elif system == "Darwin":
    result = runner.invoke(cli.sys, ['start'])
    mock.client.wait_start(0.5, 10)

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

