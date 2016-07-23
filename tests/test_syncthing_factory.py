import pytest
import json

from kdr import syncthing_factory as factory
from kdr.utils import config_rollbacker as rb
from mock import adapters as mock

Cache = {}
c_app_rb = rb.AppRollbacker(mock.client)
s_app_rb = rb.AppRollbacker(mock.server)
c_st_rb = rb.SyncthingRollbacker(mock.client)
s_st_rb = rb.SyncthingRollbacker(mock.server)

c_app_conf = json.dumps(mock.client.adapter.get_config())
s_app_conf = json.dumps(mock.server.adapter.get_config())
c_st_conf = json.dumps(mock.client.get_config())
s_st_conf = json.dumps(mock.server.get_config())

def test_make_server():
  ''' Ensure that kdr sys -s meets specs '''

  config_path = mock.client.adapter.st_conf_file
  gui_addr = mock.client.adapter.get_gui_address(config_path)
  port = gui_addr.split(':')[1]

  mock.client.make_server()

  kdr_config = mock.client.adapter.get_config()

  if 'system' not in kdr_config:
    assert False

  if 'server' not in kdr_config['system']:
    assert False

  if not kdr_config['system']['server']:
    assert False

  config_path = mock.client.adapter.st_conf_file
  gui_addr = mock.client.adapter.get_gui_address(config_path)
  expected = "0.0.0.0:%s" % port

  if gui_addr != expected:
    print "Was expecting gui address to be %s" % expected
    print "Instead got: %s" % gui_addr
    assert False

  assert True 

def test_system_client():
  ''' Ensure that kdr sys -c meets specs '''
    
  mock.client.wait_start(0.5, 10)

  config_path = mock.client.adapter.st_conf_file
  gui_addr = mock.client.adapter.get_gui_address(config_path)
  port = gui_addr.split(':')[1]

  mock.client.make_client()

  kdr_config = mock.client.adapter.get_config()

  if 'system' not in kdr_config:
    assert False

  if 'server' not in kdr_config['system']:
    assert False

  if kdr_config['system']['server']:
    assert False
  
  gui_addr = mock.client.adapter.get_gui_address(config_path)
  expected = "127.0.0.1:%s" % port
  if gui_addr != expected:
    print "Was expecting gui address to be %s" % expected
    print "Instead got: %s" % gui_addr
    assert False

  assert True

def test_add():
  ''' Ensure that kdr add meets specs '''

  mock.client.wait_start(0.5, 10)
  client_sync_dir = mock.client_conf['sync_dir']

  mock.client.add(
    path=client_sync_dir,
    tag='my-sync'
  )

  mock.client.wait_start(0.5, 10)

  folder = mock.client.find_folder({
    'path': client_sync_dir
  })

  if not folder:
    print "%s was not inserted into config['folders']" % client_sync_dir
    assert False

  # Also test if folder was added into json file

  assert True

def test_key():
  ''' Ensure that kdr key meets specs '''

  mock.client.wait_start(0.5, 10) 
  output = mock.client.encode_key(mock.client_conf['sync_dir'])

  assert len(output) > 0

def test_free_local():

  mock.client.wait_start(0.5, 10)
  client_sync_dir = mock.client_conf['sync_dir']
  mock.client.free(client_sync_dir)

def test_link_server():
  ''' Ensure that kdr link meets specs '''
  
  client_sync_dir = mock.client_conf['sync_dir']
  server_sync_dir = mock.server_conf['sync_dir']

  # Preprocess server
  if not mock.server.folder_exists({
    'path' : server_sync_dir
  }):
    r_api_key = mock.server.add(
      path=server_sync_dir,
      tag='client-sync'
    )
    mock.server.wait_start(0.5, 10)

  mock.server.make_server()
  mock.server.wait_start(0.5, 10)
  mock.client.wait_start(0.5, 10)
  key = mock.server.encode_key(server_sync_dir)
  
  # Run command on mock.client
  md = mock.client.decode_key(key)
  mock.client.link(
    device_id=md['devid'],
    api_key=md['api_key'],
    remote_path=md['remote_path'],
    local_path= client_sync_dir,
    tag='my-sync',
    remote_host='0.0.0.0',
    remote_port=mock.server_conf['port']
  )

  mock.client.wait_start(0.5, 10) 
  config = mock.client.get_config()

  # Check if src metadata was inserted
  folder = mock.client.find_folder({
    'path' : client_sync_dir
  }, config)

  if folder == None:
    print "%s was not inserted into config['folders']" % client_sync_dir
    assert False
  
  Cache['folder_id'] = folder['id']
    
  mock.server.wait_start(0.5, 10) # Wait for link remote.restart
  remote = factory.SyncthingProxy(
    md['devid'],
    '0.0.0.0',
    md['api_key'],
    port=mock.server_conf['port']
  )

  # Check device metadata was inserted locally
  inserted = mock.client.device_exists(
    remote.get_device_id(), 
    config
  )

  if not inserted:
    print "This device was not inserted into config['devices']."
    assert False
  
  # Check device metadata was inserted remotely
  r_config = remote.get_config()
  inserted = remote.device_exists(
    mock.client.get_device_id(),
    r_config
  )

  if not inserted:
    print "This device was not inserted into r_config['devices']"
    assert False
  
  # Check device was inserted into folder metadata
  r_folder = remote.find_folder({
    'id' : Cache['folder_id']
  }, r_config)
  device = remote.find_device(mock.client.get_device_id(), r_folder)
  
  if not device:
    print "This device could not be found in r_config['folders']['devices']"
    assert False

  assert True

def test_free_server():
  ''' Ensure that kdr free meets specs '''
  
  mock.client.wait_start(0.5, 10) 

  client_sync_dir = mock.client_conf['sync_dir']
  server_sync_dir = mock.server_conf['sync_dir']
  mock.client.free(client_sync_dir)

  mock.client.wait_start(0.5, 10) 
  config = mock.client.get_config()

  # Check if src metadata was deleted
  folder = mock.client.find_folder({
    'path' : client_sync_dir,
  }, config)

  if folder:
    print "%s is still in config['folders']" % client_sync_dir
    assert False
  
  # Check device metadata was deleted
  key = mock.server.encode_key(server_sync_dir)
  md = mock.client.decode_key(key)
  device = mock.client.find_device(
    md['devid'],
    config
  )

  if device:
    print "This device is still in config['devices']."
    assert False

  remote = factory.SyncthingProxy(
    md['devid'],
    '0.0.0.0',
    md['api_key'],
    port=mock.server_conf['port']
  )

  # Check device metadata was deleted
  device = mock.client.find_device(
    remote.get_device_id(), 
    config
  )

  if device:
    print "This device is still in config['devices']."
    assert False
  
  # Check device metadata was inserted remotely
  r_config = remote.get_config()
  device = remote.find_device(
    mock.client.get_device_id(),
    r_config
  )

  if device:
    print "This device is still in r_config['devices']"
    assert False
  
  # Check device was inserted into folder metadata
  r_folder = remote.find_folder({
    'id' : Cache['folder_id']
  }, r_config)
  device = remote.find_device(mock.client.get_device_id(), r_folder)
  
  if device:
    print "This device is still in r_config['folders']['devices']"
    assert False

  assert True

def test_rollback():
  c_app_rb.rollback_config()
  c_st_rb.rollback_config()
  s_app_rb.rollback_config()
  s_st_rb.rollback_config()

  c_app_conf_n = json.dumps(mock.client.adapter.get_config())
  s_app_conf_n = json.dumps(mock.server.adapter.get_config())
  c_st_conf_n = json.dumps(mock.client.get_config())
  s_st_conf_n = json.dumps(mock.server.get_config())

  if c_app_conf_n != c_app_conf:
    assert False

  if s_app_conf_n != s_app_conf:
    assert False

  if c_st_conf_n != c_st_conf:
    assert False

  if s_st_conf_n != s_st_conf_n:
    assert False

  assert True

'''
def test_cli():
    result = .invoke(cli.main)
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == 'Hello, world.'


def test_cli_with_option():
    result = .invoke(cli.main, ['--as-cowboy'])
    assert not result.exception
    assert result.exit_code == 0
    assert result.output.strip() == 'Howdy, world.'


def test_cli_with_arg():
    result = .invoke(cli.main, ['Michael'])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == 'Hello, Michael.'
'''
