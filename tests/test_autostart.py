import pytest

from click.testing import CliRunner
from kodrive import cli
from kodrive import syncthing_factory as factory

import time, os, json 
import shutil, subprocess, platform

from mock import cli as mock


# Only tests Mac OSX for now

@pytest.fixture
def runner():
  return CliRunner()

def test_autostart(runner):
  ''' Ensures that kodrive will autostart  '''

  result = runner.invoke(cli.sys, ['start'])
  mock.client.wait_start(0.5, 10)

  if result.exception:
    print result.exception
    assert False

  if not mock.client.ping():
    assert False

  kodrive_config = mock.client.adapter.get_config()
  system = platform.system()

  if system == "Linux":
    print 'Linux does not autostart yet.'
    assert True

  elif system == "Darwin":
    plist_name = 'com.kodrive.autostart'

    daemon_list = subprocess.check_output([
      'launchctl', 'list'   
    ])

    if plist_name not in daemon_list:
      print 'kodrive was not added to the autostart list'
      assert False

  result = runner.invoke(cli.sys, ['stop'])

  if result.exception:
    print result.exception
    assert False

  if system == "Linux":
    print 'Linux does not autostart yet.'
    assert True

    # if not mock.client.ping():
    #   assert False

  elif system == "Darwin":

    if mock.client.ping():
      result = runner.invoke(cli.sys, ['stop'])

      if result.exception:
        print result.exception
        assert False
  
      if mock.client.ping():
        assert False

