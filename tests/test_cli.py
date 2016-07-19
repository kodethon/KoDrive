import pytest
from click.testing import CliRunner
from kdr import cli
from kdr import syncthing_factory as factory

handler = factory.get_handler()

@pytest.fixture
def runner():
    return CliRunner()

def test_system_client(runner):
  result = runner.invoke(cli.sys, ['-c'])
  kdr_config = handler.adapter.get_config()

  if 'system' not in kdr_config:
    assert False

  if 'server' not in kdr_config['system']:
    assert False

  if kdr_config['system']['server']:
    assert False

  assert True

def test_system_server(runner):
  result = runner.invoke(cli.sys, ['-s'])
  kdr_config = handler.adapter.get_config()

  if 'system' not in kdr_config:
    assert False

  if 'server' not in kdr_config['system']:
    assert False

  if not kdr_config['system']['server']:
    assert False

  assert True



'''
def test_cli(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == 'Hello, world.'


def test_cli_with_option(runner):
    result = runner.invoke(cli.main, ['--as-cowboy'])
    assert not result.exception
    assert result.exit_code == 0
    assert result.output.strip() == 'Howdy, world.'


def test_cli_with_arg(runner):
    result = runner.invoke(cli.main, ['Michael'])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == 'Hello, Michael.'
'''
