from kodrive import syncthing_factory as factory

import os

home_dir = os.path.expanduser('~')
test_dir = os.path.join(home_dir, 'kodrive_test')
client_conf = {
  'port' : 8389,
  'sync_home' : os.path.join(test_dir, 'client'),
  'sync_dir' : os.path.join(test_dir, 'client', 'sync') + '/',
}

server_conf = {
  'port' : 8390,
  'sync_home' : os.path.join(test_dir, 'server'),
  'sync_dir' : os.path.join(test_dir, 'server', 'sync') + '/',
}

if not os.path.exists(client_conf['sync_home']):
  os.makedirs(client_conf['sync_home'])

if not os.path.exists(client_conf['sync_dir']):
  os.makedirs(client_conf['sync_dir'])

if not os.path.exists(server_conf['sync_home']):
  os.makedirs(server_conf['sync_home'])

if not os.path.exists(server_conf['sync_dir']):
  os.makedirs(server_conf['sync_dir'])

client = factory.get_handler(client_conf['sync_home'])
server = factory.get_handler(server_conf['sync_home'])

if not server.ping():
  server.start(
    delay=None,
    client=False,
    server=False,
    lcast=False,
    port=server_conf['port']
  )

if not client.ping():
  client.start(
    delay=None,
    client=False,
    server=False,
    lcast=False,
    port=client_conf['port']
  )
