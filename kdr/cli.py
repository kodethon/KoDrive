import click
import os, time, math

from . import cli_syncthing_adapter

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.version_option()
@click.group(
  epilog="Run 'kdr COMMAND --help' for more information on a command.", 
  context_settings=CONTEXT_SETTINGS
)

@click.pass_context
def main(ctx):
  ''' A tool to synchronize remote/local directories. '''
  pass

# 
# Subcommands start
#

### Sys
@main.command()
#@click.option('-k', '--key', is_flag=True, help="Return device key.")
#@click.option('-a', '--about', is_flag=True, help="List KodeDrive information.")
@click.option('-i', '--init', is_flag=True, help="Init KodeDrive daemon.")
@click.option('-e', '--exit', is_flag=True, help="Exit KodeDrive daemon.")
@click.option('-c', '--client', is_flag=True, help="Set Kodedrive into client mode.")
@click.option('-s', '--server', is_flag=True, help="Set Kodedrive into server mode.")
@click.option('-r', '--restart', is_flag=True, help="Restart KodeDrive daemon.")
@click.option('-d', '--delay', type=int, help="Set remote device detection speed.", metavar="  <INTEGER>")
#@click.option('-t', '--test', help="Test random functions :)")
def sys(**kwargs):
  ''' Manage system configuration. '''

  output, err = cli_syncthing_adapter.sys(**kwargs)
  
  if output:
    click.echo("%s" % output, err=err)
  else:
    if not kwargs['init']:
      click.echo(click.get_current_context().get_help())

### Info 
@main.command()
@click.option(
  '-d', '--device', 
  is_flag=True, 
  help="Display device information."
)
@click.option(
  '-f', '--folder', 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="<PATH>", help="Display folder information."
)
def info(**kwargs):
  ''' Display synchronization information. '''

  output, err = cli_syncthing_adapter.info(**kwargs)

  if err:
      click.echo(output, err=err)
  else:
    if kwargs['folder']:
        stat = output['status']
        click.echo("State: %s" % stat['state'])
        click.echo("\nTotal files: %s" % stat['localFiles'])
        click.echo("Files needed: %s" % stat['needFiles'])
        click.echo("\nTotal bytes: %s" % stat['localBytes'])
        click.echo("Bytes needed: %s" % stat['needBytes'])
        click.echo("\nFiles Needed:")

        files_needed = output['files_needed']['progress']
        for f in files_needed:
          click.echo("  " + f['name'])

        files_needed = output['files_needed']['queued']
        for f in files_needed:
          click.echo("  " + f['name'])

        files_needed = output['files_needed']['rest']
        for f in files_needed:
          click.echo("  " + f['name'])

    elif kwargs['device']:
      click.echo(output)
    else:
      click.echo(click.get_current_context().get_help())

### Ls
@main.command()
def ls():
  ''' List synchronized directories. '''

  heading, body = cli_syncthing_adapter.ls()
  
  if heading:
    click.echo(heading)

  if body:
    click.echo(body.strip())

### Link
@main.command()
@click.argument('key', nargs=1)
@click.option(
  '-i', '--interval', default=5,
  nargs=1, metavar="<INTEGER>",
  help="Specify sync interval."
)
@click.option(
  '-t', '--tag', nargs=1, 
  metavar="     <TEXT>", 
  help="Associate this folder with a tag."
)
@click.option(
  '-p', '--path', 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  default=".", nargs=1, metavar="    <PATH>",
  help="Specify which folder to link."
)
@click.option(
  '-y', '--yes', nargs=1, is_flag=True,
  default=False,
  help="Bypass confirmation step."
)
def link(**kwargs):
  ''' Synchronize remote/local directory. '''
  
  if kwargs['yes']:
    output, err = cli_syncthing_adapter.link(**kwargs)
    click.echo("%s" % output, err=err)
  else:
    if click.confirm("Are you sure you want to link %s?" % kwargs['path']):
      output, err = cli_syncthing_adapter.link(**kwargs)
      click.echo("%s" % output, err=err)

''' 
  *** Make the catch more specific 

  output = None

  if click.confirm("Are you sure you want to link to %s?" % path):
    try:
      output = cli_syncthing_adapter.init(key, tag, path)

    except ValueError:
      raise

    except:
      cli_syncthing_adapter.start()
      sleep(1.5)
      output = cli_syncthing_adapter.init(key, tag, path)

    finally:
      if output:
        click.echo("%s" % output)
'''

### Add
@main.command()
@click.option(
  '-t', '--tag', nargs=1, metavar=" <TEXT>", 
  default="my-sync",
  help="Associate this folder with a tag."
)
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
def add(**kwargs):
  ''' Make a folder shareable. '''

  output, err = cli_syncthing_adapter.add(**kwargs)
  click.echo("%s" % output, err=err)

### Free
@main.command()
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
def free(**kwargs):
  ''' Stop synchronization of directory. '''

  output, err = cli_syncthing_adapter.free(kwargs['path'])
  click.echo("%s" % output, err=err)

### Tag
"""
@main.command()
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
@click.argument('name', nargs=1)
def tag(path, name):
  ''' Change tag associated with directory. '''

  output, err = cli_syncthing_adapter.tag(path, name)
  click.echo("%s" % output, err=err)
"""

### Key
@main.command()
@click.option(
  '-d', '--device', 
  is_flag=True, 
  help="Display device key."
)
@click.option(
  '-f', '--folder', 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="<PATH>", help="Display folder key."
)
def key(**kwargs):
  ''' Display synchronization key. '''

  output, err = cli_syncthing_adapter.key(**kwargs)

  if not output:
    click.echo(click.get_current_context().get_help())
  else:  
    click.echo("%s" % output, err=err)

### Mv
@main.command()
@click.argument('source', nargs=-1, required=True)
@click.argument('target', nargs=1)
def mv(source, target):
  ''' Move synchronized directory. '''

  if os.path.isfile(target) and len(source) == 1:
    if click.confirm("Are you sure you want to overwrite %s?" % target):

      err_msg = cli_syncthing_adapter.mv_edge_case(source, target)
      # Edge case: to match Bash 'mv' behavior and overwrite file

      if err_msg:
        click.echo(err_msg)

      return

  if len(source) > 1 and not os.path.isdir(target):
    click.echo(click.get_current_context().get_help())
    return

  else:
    err_msg, err = cli_syncthing_adapter.mv(source, target)

    if err_msg:
      click.echo(err_msg, err)

### Auth
@main.command()
@click.option(
  '-a', '--add', 
  type=(str, (click.Path(exists=True, writable=True, resolve_path=True))), 
  default=(None, None), nargs=2, metavar="   <KEY> <PATH>",
  help="Authorize a directory."
)
@click.option(
  '-r', '--remove', 
  type=(str, (click.Path(exists=True, writable=True, resolve_path=True))), 
  default=(None, None), nargs=2, metavar="<KEY> <PATH>",
  help="Deauthorize a directory."
)
@click.option(
  '-l', '--list', 
  is_flag=True, 
  help="List all devices authorized")
@click.option(
  '-y', '--yes', nargs=1, is_flag=True,
  default=False,
  help="Bypass confirmation step."
)
def auth(**kwargs):
  ''' Authorize device synchronization. '''

  """
    kdr auth <path> <device_id (client)>

    1. make sure path has been added to config.xml, server
    2. make sure path is not shared by someone
    3. add device_id to folder in config.xml, server
    4. add device to devices in config.xml, server

  """
  output = None
  option = None
  path = None
  key = None

  if all(kwargs['add']): # if tuple doesn't contain all Nones
    (key, path) = kwargs['add']
    option = 'add'

  elif all(kwargs['remove']):
    (key, path) = kwargs['remove']
    option = 'remove'

  elif kwargs['list']:
    option = 'list'
    output, err = cli_syncthing_adapter.auth(option, key, path)

    if output:
      click.echo("%s" % output, err=err)

    return

  if kwargs['yes']:
    output, err = cli_syncthing_adapter.auth(option, key, path)
    click.echo("%s" % output, err=err)

  else:
    if all(kwargs['add']): 
      if click.confirm("Are you sure you want to authorize this device to access %s?" % path):
        output, err = cli_syncthing_adapter.auth(option, key, path)

      else:
        return

    else:
      output, err = cli_syncthing_adapter.auth(option, key, path)

  if output:
    click.echo("%s" % output, err=err)
  
  if not output or not option:
    click.echo(click.get_current_context().get_help())

### Push
@main.command()
@click.option(
  '-v', '--verbose', is_flag=True,
  help='Show synchronize progress.'
)
@click.argument(
  'path', nargs=1, 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
)
def push(**kwargs):
  ''' Force synchronization of directory. '''

  output, err = cli_syncthing_adapter.refresh(**kwargs)

  if output:
    click.echo("%s" % output, err=err)

  if kwargs['verbose'] and not err:
    with click.progressbar(
      iterable=None,
      length=100,
      label='Synchronizing') as bar:

      device_num = 0
      max_devices = 1
      prev_percent = 0

      while True:
        kwargs['progress'] = True
        kwargs['device_num'] = device_num
        data, err = cli_syncthing_adapter.refresh(**kwargs)

        device_num = data['device_num']
        max_devices = data['max_devices']

        cur_percent = math.floor(data['percent']) - prev_percent
        if cur_percent > 0:
          bar.update(cur_percent)
          prev_percent = math.floor(data['percent'])

        if device_num < max_devices:
          time.sleep(0.5)
        else:
          break


"""
REFERENCE

@main.command()
@click.option(
  '-p', '--port', nargs=1, 
  type=int
)
@click.option(
  '-c', '--config', nargs=1, 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
)
def start(**kwargs):
  ''' Start a KodeDrive instance. '''
  output = cli_syncthing_adapter.start(**kwargs)
  click.echo("%s" % output)  

@main.command()
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
def inspect(path):
  ''' Return information regarding directory. '''

  return

@main.command()
@click.argument('arg', nargs=1)
def test(arg):
  ''' Test random functions :) '''

  cli_syncthing_adapter.test(arg)

@cli.command()
@click.argument('src', type=click.Path(exists=True), nargs=1)
@click.argument('dest', nargs=1)
def connect(src, dest):
  ''' Connect to remote server. '''
    
  output = cli_syncthing_adapter.connect()
  click.echo("%s" % output)

@click.group(invoke_without_command=True)
@click.option('-v', '--version', is_flag=True, help='Print version information and quit')
click.echo("%s '%s' is not a valid command." % ('kodedrive:', arg))
click.echo("See 'kodedrive --help'.")

@main.command()
def start():
  ''' Start KodeDrive daemon. '''

  output = cli_syncthing_adapter.start()
  click.echo("%s" % output)

@main.command()
def stop():
  ''' Stop KodeDrive daemon. '''

  output = cli_syncthing_adapter.stop()
  output = output.strip()
  click.echo("%s" % output)

@main.command()
@click.argument('arg', nargs=1)
def test(arg):
  ''' Test random functions :) '''

  cli_syncthing_adapter.test(arg)

Syncthing's scan currently seems buggy


"""
