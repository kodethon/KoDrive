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

def test_init_conf():

  mock.client.wait_start(0.5, 10)
  config= mock.client.get_config()
  ris = config['options']['reconnectionIntervalS']
  rrim = config['options']['relayReconnectIntervalM']

  if not ris == 5:
    print "Was expecting reconnectionIntervalS to be %s" % 5
    print "Instead got: %s" % ris
    assert False

  if not rrim == 0:
    print "Was expecting relayReconnectionIntervalM to be %s" % 0
    print "Instead got: %s" % rrim
    assert False

  kdr_config = mock.client.adapter.get_config()
  devid = mock.client.get_device_id()

  if not kdr_config['system']['devid'] == devid:
    print "Was expecting %s to be in app config." % devid
    print "Instead got: %s" % kdr_config['system']['devid']
    assert False

def test_make_server():
  ''' Ensure that syncthing_ meets specs '''

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

  # mock.client.wait_start(0.5, 10)
  client_sync_dir = mock.client_conf['sync_dir']
  mock.client.free(client_sync_dir)

def test_link_server():
  ''' Ensure that kdr link meets specs '''
  
  client_sync_dir = mock.client_conf['sync_dir']
  server_sync_dir = mock.server_conf['sync_dir']

  # Preprocess server
  mock.server.wait_start(0.5, 10)
  mock.server.add(
    path=server_sync_dir,
    tag='client-sync'
  )
  mock.server.wait_start(0.5, 10)

  mock.server.make_server()
  mock.server.wait_start(0.5, 10)
  key = mock.server.encode_key(server_sync_dir)
  
  # Run command on mock.client
  md = mock.client.decode_key(key)
  mock.client.wait_start(0.5, 10)

  mock.client.link(
    device_id=md['devid'],
    api_key=md['api_key'],
    remote_path=md['remote_path'],
    local_path= client_sync_dir,
    tag='my-sync',
    remote_host='0.0.0.0',
    remote_port=mock.server_conf['port']
  )

  mock.server.wait_start(0.5, 10) # Wait for link remote.restart
  mock.client.wait_start(0.5, 10)
  mock.server.wait_sync(0.5, 10)
  mock.client.wait_sync(0.5, 10)
  remote = factory.SyncthingProxy(
    md['devid'],
    '0.0.0.0',
    md['api_key'],
    port=mock.server_conf['port']
  )
  
  # Check Remote ~~~

  # Check device metadata was inserted remotely
  r_config = remote.get_config()
    
  c_devid = mock.client.get_device_id()
  
  inserted = False
  for d in r_config['devices']:
    if d['deviceID'] == c_devid:
      inserted = True

  if not inserted:
    print "This device was not inserted into r_config['devices']"
    log_configs([r_config])
    assert False
  
  # Check device was inserted into folder metadata
  r_folder = remote.find_folder({
    'path' : server_sync_dir
  }, r_config)
  device = remote.find_device(mock.client.get_device_id(), r_folder)
  
  if not device:
    print "This device could not be found in r_config['folders']['devices']"
    assert False
  
  # Check Client ~~~

  # Check device metadata was inserted locally
  config = mock.client.get_config()
  inserted = mock.client.device_exists(
    remote.get_device_id(), 
    config
  )

  if not inserted:
    print "This device was not inserted into config['devices']."
    assert False

  folder_found = False  
  for f in config['folders']:
    if client_sync_dir.rstrip('/') == f['path'].rstrip('/'):
      folder_found = True
      break

  if not folder_found:
    print "%s was not inserted into config['folders']" % client_sync_dir
    log_configs([config])
    assert False

  assert True

def test_free_server():
  ''' Ensure that kdr free meets specs '''
  
  mock.client.wait_start(0.5, 10) 

  client_sync_dir = mock.client_conf['sync_dir']
  server_sync_dir = mock.server_conf['sync_dir']
  mock.client.free(client_sync_dir)

  # mock.client.wait_start(0.5, 10)
  # mock.server.wait_start(0.5, 10)
  mock.server.wait_sync(0.5, 10)
  mock.client.wait_sync(0.5 ,10)
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
    print config
    assert False
  
  # Check device metadata was deleted remotely
  r_config = remote.get_config()
  devid = mock.client.get_device_id()
  device_inserted = False
  for d in r_config['devices']:
    if d['deviceID'] == devid:
      device_inserted = True
    
  if device_inserted:
    print "Found %s in r_config['devices']" % devid
    print r_config
    assert False
  
  # Check device was deleted from folder metadata
  r_folder = remote.find_folder({
    'path' : server_sync_dir
  }, r_config)
  device = remote.find_device(mock.client.get_device_id(), r_folder)
  
  if device:
    print "This device is still in r_config['folders']['devices']"
    assert False

  assert True

def test_auth():
  ''' Ensure that kdr auth meets specs '''

  mock.client.make_client()
  mock.client.wait_start(0.5, 10)

  mock.server.make_client()
  mock.server.wait_start(0.5, 10)

  syncthing_config = mock.client.get_config()
  kdr_config = mock.client.adapter.get_config()

  mock.client.wait_start(0.5, 10)
  client_sync_dir = mock.client_conf['sync_dir']
  test_device_id = mock.server.get_device_id()
  test_device_key = mock.server.encode_device_key()

  if mock.client.folder_exists({
    'path' : client_sync_dir
  }):
    mock.client.wait_start(0.5, 10)
    mock.client.free(client_sync_dir)

  mock.client.wait_start(0.5, 10)

  if mock.client.device_exists(test_device_id):
    # mock.client.wait_start(0.5, 10)
    mock.client.delete_device(test_device_id, syncthing_config)

  mock.client.wait_start(0.5, 10)
  
  mock.client.add(
    path=client_sync_dir,
    tag='my-sync'
  )

  mock.client.wait_start(0.5, 10)

  folder = mock.client.find_folder({
    'path' : client_sync_dir
  })

  if not folder:
    print "%s was not inserted into config['folders']" % client_sync_dir
    c_app_rb.rollback_config()
    c_st_rb.rollback_config()
    assert False

  for k in kdr_config['directories']:
    f = kdr_config['directories'][k]

    if f['local_path']  == client_sync_dir.rstrip('/'):
      if f['is_shared']:
        print 'This file is already shared.'
        assert False

  mock.client.wait_start(0.5, 10)
  mock.client.auth(test_device_key, client_sync_dir)

  mock.client.wait_start(0.5, 10)

  if not mock.client.device_exists_in_folder(client_sync_dir, test_device_id):

    print "%s was not added to the folder\n" % test_device_id
    print "Devices authorized to access %s:" % client_sync_dir

    for devid in folder['devices']:
      print "\t%s" % devid['deviceID']

    mock.client.wait_start(0.5, 10)
    c_app_rb.rollback_config()
    c_st_rb.rollback_config()
    assert False

  # mock.client.wait_start(0.5, 10)

  if not mock.client.device_exists(test_device_id):
    print "%s was not added to the devices" % test_device_id
    assert False

  assert True

def test_deauth():
  ''' Ensure that kdr deauth meets specs '''

  mock.client.wait_start(0.5, 10)
  mock.client.make_client()
  mock.client.wait_start(0.5, 10)
  mock.server.make_client()
  mock.server.wait_start(0.5, 10)

  syncthing_config = mock.client.get_config()
  kdr_config = mock.client.adapter.get_config()

  client_sync_dir = mock.client_conf['sync_dir']
  test_device_id = mock.server.get_device_id()
  test_device_key = mock.server.encode_device_key()

  mock.client.wait_start(0.5, 10)
  mock.client.deauth(test_device_key, client_sync_dir)

  # mock.client.wait_start(0.5, 10)

  if mock.client.device_exists_in_folder(client_sync_dir, test_device_id):

    print "%s was not removed from the folder." % test_device_id
    # mock.client.wait_start(0.5, 10)
    c_app_rb.rollback_config()
    c_st_rb.rollback_config()

    assert False

  r_devid = {
    u'deviceID' : test_device_id
  }

  in_other_folders = False

  for f in syncthing_config['folders']:
    if r_devid in f['devices'] and client_sync_dir != f['path']:
      in_other_folders = True
      break

  if mock.client.device_exists(test_device_id) and not in_other_folders:

    print "%s was not removed from devices" % test_device_id
    mock.client.wait_start(0.5, 10)
    c_app_rb.rollback_config()
    c_st_rb.rollback_config()

    assert False

  mock.client.wait_start(0.5, 10)
  mock.client.free(client_sync_dir)

  assert True

def test_rollback():
  mock.client.wait_start(0.5, 10)

  c_app_rb.rollback_config()
  c_st_rb.rollback_config()
  s_app_rb.rollback_config()
  s_st_rb.rollback_config()

  c_app_conf_n = json.dumps(mock.client.adapter.get_config())
  s_app_conf_n = json.dumps(mock.server.adapter.get_config())
  c_st_conf_n = json.dumps(mock.client.get_config())
  s_st_conf_n = json.dumps(mock.server.get_config())

  mock.server.wait_start(0.5, 10)
  mock.client.wait_start(0.5, 10)

  if c_app_conf_n != c_app_conf:
    assert False

  if s_app_conf_n != s_app_conf:
    assert False

  if c_st_conf_n != c_st_conf:
    assert False

  if s_st_conf_n != s_st_conf_n:
    assert False

  assert True

def log_configs(configs):
  for c in configs:
    print c

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
