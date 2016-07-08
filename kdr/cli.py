import click
import cli_syncthing_adapter
import os
import json
import platform
import xml.etree.ElementTree as ET
from time import sleep


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.version_option()
@click.group(
  epilog="Run 'kdr COMMAND --help' for more information on a command.", 
  context_settings=CONTEXT_SETTINGS
  #add_help_option=False, 
  #options_metavar="\b",
)

@click.pass_context
def main(ctx):
  ''' A tool to synchronize remote/local directories. '''
  pass

# 
# Subcommands start
#

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
@click.option('-a', '--all', is_flag=True, help="Display all application information.")
@click.option('-s', '--status', is_flag=True, help="Return daemon status.")
@click.option('-k', '--key', is_flag=True, help="Display KodeDrive key.")
def info(**kwargs):
  ''' Display application information. '''

  is_default = True
  
  for opt in kwargs:
    if kwargs[opt]:
      is_default = False

  if is_default:
    click.echo(click.get_current_context().get_help())

  else:
    output = cli_syncthing_adapter.info(**kwargs)
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
@click.option(
  '--path', type=click.Path(exists=True), 
  default=".", nargs=1, metavar="<PATH>",
  help="Specify a folder."
)

def ls(path):
  ''' List synchronized directories. '''

  home_dir = os.path.expanduser('~')
  folder_path = os.path.join(home_dir, '.config/kdr')

  with open(folder_path + "/config.json") as f:
    data = json.load(f)
    # data is a dictionary containing a list of dictionaries

  dirs = data['directories'] # type: list

  click.echo("{:<50}".format('Directory names:') + 'Paths:')

  for i, val in enumerate(dirs): # for each item in the list
    for key, value in val.iteritems(): # for each dictionary in each item
      try:
        click.echo("{:<50}".format(key) + value['local_path'])
      except:
        click.echo("{:<50}".format(key) + value[key]['local_path'])

  return

@main.command()
@click.argument('key', nargs=1)
@click.option(
  '-t', '--tag', nargs=1, metavar="<TEXT>", 
  help="Associate this folder with a tag."
)
@click.option(
  '-p', '--path', 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  default=".", nargs=1, metavar="<PATH>",
  help="Specify which folder to link."
)
def link(key, tag, path):
  ''' Synchronize remote/local directory. '''

  if click.confirm("Are you sure you want to link to %s?" % path):
    output = cli_syncthing_adapter.link(key, tag, path)
    click.echo("%s" % output)

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

@main.command()
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
def unlink(**kwargs):
  ''' Stop synchronization of directory. '''

  output = cli_syncthing_adapter.unlink(kwargs['path'])
  click.echo("%s" % output)


@main.command()
@click.argument('cur', nargs=1)
@click.argument('new', nargs=1)
def retag(cur, new):
  ''' Change tag associated with directory. '''
  return

@main.command()
@click.argument('arg', nargs=1)
def test(arg):
  ''' Test random functions :) '''

  cli_syncthing_adapter.test(arg)

"""
Syncthing's scan currently seems buggy

@main.command()
@click.option(
  '-v', '--verbose', is_flag=True,
  help='Show synchronize progress.'
)
@click.argument(
  'path', nargs=1, 
  type=click.Path(exists=True, writable=True, resolve_path=True), 
)
def refresh(**kwargs):
  ''' Force synchronization of directory. '''

  output = cli_syncthing_adapter.refresh(**kwargs)

  if output:
    click.echo("%s" % output)

  if kwargs['verbose']:
    with click.progressbar(
      length=100,
      label='Synchronizing') as bar:

      progress = 0

      while not progress == 100:
        progress = cli_syncthing_adapter.refresh(progress=True)
"""

@main.command()
@click.argument('cur', nargs=1)
@click.argument('new', nargs=1)
def retag(cur, new):
    ''' Change tag associated with directory. '''

    return

@main.command()
@click.argument('source', nargs=1)
@click.argument('target', nargs=1)
def mv(source, target):
  ''' Rename directory. '''

  if os.path.isdir(target) or os.path.islink(target):
    move(source, target)
    # if target is an existing directory or symbolic link then move()

  else:
    cli_syncthing_adapter.rename(source, target)

  return

@main.command()
@click.argument('arg', nargs=1)
def test(arg):
  ''' Test random functions :) '''

  cli_syncthing_adapter.test(arg)

"""

REFERENCE

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

"""
