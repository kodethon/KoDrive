import pytest

from click.testing import CliRunner
from kodrive import cli
from kodrive import syncthing_factory as factory

import time, os, json, shutil

from mock import cli as mock

@pytest.fixture
def runner():
  return CliRunner()

def test_system_init(runner):
  ''' Ensure that syncthing is up '''
  
  result = runner.invoke(cli.sys, ['start'])
  mock.client.wait_start(0.5, 10)

  if result.exception:
    print result.exception
    print result.output
    assert False

  assert mock.client.ping()

def test_system_exit(runner):
  ''' Ensure that syncthing is down '''

  result = runner.invoke(cli.sys, ['stop'])

  if result.exception:
    print result.exception
    assert False

def test_mv_rename(runner):
  """
    1. 'kodrive add' a path to the json
    2. rename it
    3. check if rename worked
    4. if worked, revert and 'kodrive free', else False
  """

  source_dir = os.path.join(mock.client.adapter.home_dir, 'Downloads', 'THE_CHOSEN_ONE')
  target_dir = os.path.join(mock.client.adapter.home_dir, 'Downloads', 'NOT_THE_CHOSEN_ONE')

  test_system_init(runner)
  # mock.client.wait_start(0.5, 10)

  if not os.path.exists(source_dir):
    os.makedirs(source_dir)

    if not os.path.exists(source_dir):
      print "Failed to create %s" % source_dir
      assert False

  result = runner.invoke(cli.dir, ['add', source_dir])

  if result.exception:
    print result.exception
    assert False

  # mock.client.wait_start(0.5, 10)

  result = runner.invoke(cli.dir, ['mv', source_dir, target_dir])

  if result.exception:
    print result.exception
    assert False

  # mock.client.wait_start(0.5, 10)

  if not os.path.exists(target_dir) or os.path.exists(source_dir):
    print "Failed to rename %s to %s" % (source_dir, target_dir)
    assert False

  syncthing_config = mock.client.get_config()
  kodrive_config = mock.client.adapter.get_config()
  folders = syncthing_config['folders']
  old_key = mock.client.adapter.get_dir_id(source_dir)
  new_key = mock.client.adapter.get_dir_id(target_dir)
  found = False

  for f in folders:
    if target_dir == os.path.abspath(f['path']):

      if new_key != f['id']:
        print 'New folder id has failed to be added'
        assert False

      if f['id'] == old_key:
        print 'Old folder id is still there'
        assert False

      found = True
      break

  if not found:
    print 'New path hasn\'t been added to syncthing_config'
    assert False

  if new_key not in kodrive_config['directories'] or old_key in kodrive_config['directories']:
    print 'Modifying kodrive_config has failed'
    assert False

  result = runner.invoke(cli.dir, ['free', target_dir])

  if result.exception:
    print result.exception
    assert False

  # mock.client.wait_start(0.5, 10)

  shutil.rmtree(source_dir, ignore_errors=True)
  shutil.rmtree(target_dir, ignore_errors=True)

  assert True

def test_mv_move(runner):
  """
    1. 'kodrive add' a path to the json
    2. move it into another directories
    3. check if move worked
    4. if worked, revert and 'kodrive free', else False
  """

  source_dir = os.path.join(mock.client.adapter.home_dir, 'Downloads', 'child123123')
  target_dir = os.path.join(mock.client.adapter.home_dir, 'Downloads', 'parent123123')
  final_dir = os.path.join(mock.client.adapter.home_dir, 'Downloads', 'parent123123', 'child123123')

  test_system_init(runner)
  # mock.client.wait_start(0.5, 10)

  if not os.path.exists(source_dir):
    os.makedirs(source_dir)

    if not os.path.exists(source_dir):
      print "Failed to create %s" % source_dir
      assert False

  if not os.path.exists(target_dir):
    os.makedirs(target_dir)

    if not os.path.exists(target_dir):
      print "Failed to create %s" % target_dir
      assert False

  result = runner.invoke(cli.dir, ['add', source_dir])

  if result.exception:
    print result.exception
    assert False

  # mock.client.wait_start(0.5, 10)
  result = runner.invoke(cli.dir, ['mv', source_dir, target_dir])

  if result.exception:
    print result.exception
    assert False

  # mock.client.wait_start(0.5, 10)

  if os.path.exists(source_dir):
    print source_dir
    print 'source_dir was not deleted'
    assert False

  if not os.path.exists(final_dir):
    print "Failed to move %s to %s, %s doesn't exist" % (source_dir, target_dir, final_dir)
    assert False

  syncthing_config = mock.client.get_config()
  kodrive_config = mock.client.adapter.get_config()
  folders = syncthing_config['folders']
  old_key = mock.client.adapter.get_dir_id(source_dir)
  new_key = mock.client.adapter.get_dir_id(final_dir)
  found = False

  for f in folders:
    if final_dir == os.path.abspath(f['path']):

      if new_key != f['id']:
        print 'New folder id has failed to be added'
        assert False

      if f['id'] == old_key:
        print 'Old folder id is still there'
        assert False

      found = True
      break

  if not found:
    print 'New path hasn\'t been added to syncthing_config'
    assert False

  if new_key not in kodrive_config['directories'] or old_key in kodrive_config['directories']:
    print 'Modifying kodrive_config has failed'
    assert False

  result = runner.invoke(cli.dir, ['free', final_dir])

  if result.exception:
    print result.exception
    assert False

  # mock.client.wait_start(0.5, 10)

  shutil.rmtree(source_dir, ignore_errors=True)
  shutil.rmtree(target_dir, ignore_errors=True)
  shutil.rmtree(final_dir, ignore_errors=True)

  assert True

