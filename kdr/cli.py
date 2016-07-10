import click
import cli_syncthing_adapter
import os
import json

#import platform
#import xml.etree.ElementTree as ET
#from time import sleep


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

@main.command()
@click.option('-c', '--check', is_flag=True, help="Check daemon status.")
@click.option('-k', '--key', is_flag=True, help="Display KodeDrive key.")
@click.option('-s', '--start', is_flag=True, help="Start KodeDrive daemon.")
@click.option('-e', '--exit', is_flag=True, help="Exit KodeDrive daemon.")
@click.option('-t', '--test', help="Test random functions :)")
def sys(**kwargs):
  ''' Manage application administration. '''

  output = cli_syncthing_adapter.sys(**kwargs)

  if output:
    click.echo("%s" % output)
  else:
    click.echo(click.get_current_context().get_help())



@main.command()
@click.option(
  '--path', type=click.Path(exists=True), 
  default=".", nargs=1, metavar="<PATH>",
  help="Specify a folder."
)
def ls(path):
  ''' List synchronized directories. '''

  metadata = cli_syncthing_adapter.ls(path)
  
  headers = []
  lengths = []
  
  # Preprocess

  # Iterate through list
  for i, record in enumerate(metadata):
    lengths.append(0)

    # Iterate through dictionary
    for header in record:
      headers.append(header)
      num_data = len(record[header])

      for data in record[header]:
        cur = len(data)
        prev = lengths[i] 

        lengths[i] = cur if cur > prev else prev
  
  # Process
  body = str()
  for i in range(0, num_data):
    for n in range(0, len(metadata)):
      value = metadata[n][headers[n]][i]
      s = "{:<%i}" % (lengths[n] + 5)
      body += s.format(value.strip())

  heading = str()
  # Iterate through list
  for i, record in enumerate(metadata):
    # Iterate through dictionary
    for header in record:
      s = "{:<%i}" % (lengths[i] + 5)
      heading += s.format(header)
  
  # Postprocess
  click.echo(heading)
  click.echo(body)

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

  if click.confirm("Are you sure you want to link %s?" % path):
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
def free(**kwargs):
  ''' Stop synchronization of directory. '''

  output = cli_syncthing_adapter.unlink(kwargs['path'])
  click.echo("%s" % output)

@main.command()
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
@click.argument('name', nargs=1)
def tag(path, name):
  ''' Change tag associated with directory. '''

  output = cli_syncthing_adapter.tag(path, name)
  click.echo("%s" % output)

@main.command()
@click.argument(
  'path',
  type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
def key(path):
  ''' Displays synchronization key for directories. '''

  output = cli_syncthing_adapter.key(path)
  click.echo("%s" % output)

@main.command()
@click.argument('source', nargs=1)
@click.argument('target', nargs=1)
def mv(source, target):
  ''' Move synchronized directory. '''

  if os.path.isdir(target) or os.path.islink(target):
    move(source, target)
    # if target is an existing directory or symbolic link then move()

  else:
    cli_syncthing_adapter.rename(source, target)

"""
REFERENCE

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
