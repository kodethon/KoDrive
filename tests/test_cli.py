import pytest
from click.testing import CliRunner

from kdr import cli
from kdr import syncthing_factory as factory

import time, os, json

client = factory.get_handler()
mock = {
  'src' : os.path.join(client.adapter.home_dir, 'Downloads', 'node-0'),
  'r_api_key' : 'X3LIG67-PPJRAAF-TZB6HY3-5LZ7T4O-6YLBHXA-DSWB5FI-443ENUL-W2N3BAJ@/home/jvlarble/sandbox/my-sync/@tdL97duU7ZXwxpJMZ6uiqdmtkq2DAefo',
  'host' : '',
  'folder_id' : ''
}

@pytest.fixture
def runner():
  return CliRunner()

def test_system_init(runner):
  result = runner.invoke(cli.sys, ['-i'])

  assert client.ping()

def test_system_server(runner):
  
  result = runner.invoke(cli.sys, ['-s'])

  if result.exception:
    print result.exception
    assert False

  kdr_config = client.adapter.get_config()

  if 'system' not in kdr_config:
    assert False

  if 'server' not in kdr_config['system']:
    assert False

  if not kdr_config['system']['server']:
    assert False

  config_path = client.adapter.st_conf_file
  gui_addr = client.adapter.get_gui_address(config_path)

  if gui_addr != '0.0.0.0:8384':
    print 'Was expecting gui address to be 0.0.0.0:8384'
    print "Instead got: %s" % gui_addr
    assert False

  assert True 

def test_system_client(runner):

  while not client.ping():
    time.sleep(0.5)

  result = runner.invoke(cli.sys, ['-c'])

  if result.exception:
    print result.exception
    assert False

  kdr_config = client.adapter.get_config()

  if 'system' not in kdr_config:
    assert False

  if 'server' not in kdr_config['system']:
    assert False

  if kdr_config['system']['server']:
    assert False
  
  config_path = client.adapter.st_conf_file
  gui_addr = client.adapter.get_gui_address(config_path)
  if gui_addr != '127.0.0.1:8384':
    assert False

  assert True

def test_link_server(runner):
  
  while not client.ping():
    time.sleep(0.5)

  if not os.path.exists(mock['src']):
    assert False
  
  result = runner.invoke(cli.link, ['-y', '-p', mock['src'], mock['r_api_key']])

  if result.exception:
    print result.exception
    assert False

  while not client.ping():
    time.sleep(0.5)
  
  config = client.get_config()

  # Check if src metadata was inserted
  folder = client.find_folder({
    'path' : mock['src'] + '/',
  }, config)

  if not folder:
    print "%s was not inserted into config['folders']" % mock['src']
    assert False
  
  mock['folder_id'] = folder['id']

  md = client.decode_key(mock['r_api_key'])
  mock['host'] = client.devid_to_ip(md['devid'])
  remote = factory.SyncthingProxy(
    md['devid'],
    mock['host'],
    md['api_key']
  )

  # Check device metadata was inserted locally
  device = client.find_device(
    remote.get_device_id(), 
    config
  )

  if not device:
    print "This device was not inserted into config['devices']."
    assert False
  
  # Check device metadata was inserted remotely
  r_config = remote.get_config()
  device = remote.find_device(
    client.get_device_id(),
    r_config
  )

  if not device:
    print "This device was not inserted into r_config['devices']"
    assert False
  
  # Check device was inserted into folder metadata
  r_folder = remote.find_folder({
    'id' : mock['folder_id']
  }, r_config)
  device = remote.find_device(client.get_device_id(), r_folder)
  
  if not device:
    print "This device could not be found in r_config['folders']['devices']"
    assert False

  assert True

def test_free_server(runner):

  while not client.ping():
    time.sleep(0.25)
  
  result = runner.invoke(cli.free, [mock['src']])

  if result.exception:
    print result.exception
    assert False

  while not client.ping():
    time.sleep(0.25) 

  config = client.get_config()

  # Check if src metadata was deleted
  folder = client.find_folder({
    'path' : mock['src'],
  }, config)

  if folder:
    print "%s was inserted into config['folders']" % mock['src']
    assert False
  
  # Check device metadata was deleted
  md = client.decode_key(mock['r_api_key'])
  device = client.find_device(
    md['devid'],
    config
  )

  if device:
    print "This device was inserted into config['devices']."
    assert False

  remote = factory.SyncthingProxy(
    md['devid'],
    mock['host'],
    md['api_key']
  )
  r_config = remote.get_config()
  device = remote.find_device(
    client.get_device_id(),
    r_config
  )

  if device:
    print "This device was found in r_config['folders']['devices']"
    assert False

  r_folder = remote.find_folder({
    'id' : mock['folder_id']
  }, r_config)
  device = remote.find_device(client.get_device_id(), r_folder)

  if device:
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
