import pytest

from click.testing import CliRunner
from kdr import cli

from mock import cli as mock

@pytest.fixture
def runner():
  return CliRunner()

def test_system_init(runner):
  ''' Ensure that syncthing is up '''
  
  result = runner.invoke(cli.sys, ['-i'])
  mock.client.wait_start(0.5, 10)

  if result.exception:
    print result.exception
    assert False

  assert mock.client.ping()

def test_system_exit(runner):
  ''' Ensure that syncthing is down '''

  result = runner.invoke(cli.sys, ['-e'])

  if result.exception:
    print result.exception
    assert False

  assert not mock.client.ping()
