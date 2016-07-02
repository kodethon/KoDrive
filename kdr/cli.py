import click
import cli_syncthing_adapter

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.version_option()
@click.group(
    epilog="Run 'kdr COMMAND --help' for more information on a command.", 
    context_settings=CONTEXT_SETTINGS
    #add_help_option=False, 
    #options_metavar="\b",
)

@click.pass_context
def cli(ctx):
    ''' A tool to synchronize remote/local directories. '''
    pass

# 
# Subcommands start
#

@cli.command()
def start(test):
    ''' Start KodeDrive daemon. '''

    output = cli_syncthing_adapter.start()
    click.echo("%s" % output)

@cli.command()
def stop():
    ''' Stop KodeDrive daemon. '''

    output = cli_syncthing_adapter.stop()
    output = output.strip()
    click.echo("%s" % output)

@cli.command()
def info():
    ''' Display application information. '''

    output = cli_syncthing_adapter.config()
    click.echo("%s" % output)

@cli.command()
@click.argument('name', nargs=1)
def inspect(name):
    ''' Return information regarding local directory. '''
    return

@cli.command()
def status():
    ''' Determine if KodeDrive is up. '''

    output = cli_syncthing_adapter.status()
    click.echo("%s" % output)

@cli.command()
@click.option(
    '--path', type=click.Path(exists=True), 
    default=".", nargs=1, metavar="<PATH>",
    help="Specify a folder.")
def ls(path):
    ''' List synchronized directories. '''
    
    return

@cli.command()
@click.argument('key', nargs=1)
@click.option('-n', '--name', nargs=1, metavar="<TEXT>", help="Associate this folder with a name.")
@click.option(
    '-p', '--path', type=click.Path(exists=True, writable=True, resolve_path=True), 
    default=".", nargs=1, metavar="<PATH>",
    help="Specify which folder to sync to."
)
def init(key, name, path):
    ''' Synchronize remote/local directory. '''

    output = cli_syncthing_adapter.init(key, name, path)
    click.echo("%s" % output)

@cli.command()
@click.argument('arg', nargs=1)
def test(arg):
    ''' Test random functions :) '''

    cli_syncthing_adapter.test(arg)

cli()

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
