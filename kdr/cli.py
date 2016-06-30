import click
import syncthing_adapter

@click.version_option()
@click.group(
    epilog="Run 'kdr COMMAND --help' for more information on a command.", 
    #add_help_option=False, 
    #options_metavar="\b",
)

@click.pass_context

def cli(ctx):
    ''' Synchronize remote files with local directory. '''
    pass

# 
# Subcommands start
#

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option('--test')
def start(test):
    ''' Start KodeDrive daemon. '''

    output = syncthing_adapter.start()
    click.echo("%s" % output)

@cli.command(context_settings=CONTEXT_SETTINGS)
def stop():
    ''' Stop KodeDrive daemon. '''

    output = syncthing_adapter.stop()
    output = output.strip()
    click.echo("%s" % output)

@cli.command(context_settings=CONTEXT_SETTINGS)
def inspect():
    ''' Return low-level information. '''

    output = syncthing_adapter.config()
    click.echo("%s" % output)

@cli.command(context_settings=CONTEXT_SETTINGS)
def status():
    ''' Determine if KodeDrive is up. '''

    output = syncthing_adapter.status()
    click.echo("%s" % output)

@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--path', type=click.Path(exists=True), 
    default=".", nargs=1, metavar="<PATH>",
    help="Specify a folder.")
def name(path):
    ''' Display KodeDrive name associated with folder. '''
    
    return

@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument('key', nargs=1)
@click.option('-n', '--name', nargs=1, metavar="<TEXT>", help="Associate this folder with a name.")
@click.option(
    '-p', '--path', type=click.Path(exists=True, writable=True, resolve_path=True), 
    default=".", nargs=1, metavar="<PATH>",
    help="Specify which folder to sync to."
)
def init(key, name, path):
    ''' Initialize folder to sync with remote folder. '''

    output = syncthing_adapter.init(key, name, path)
    click.echo("%s" % output)

@cli.command()
def test():
    output = syncthing_adapter.test()
    click.echo("%s" % output)

cli()

"""
REFERENCE

@cli.command()
@click.argument('src', type=click.Path(exists=True), nargs=1)
@click.argument('dest', nargs=1)
def connect(src, dest):
    ''' Connect to remote server. '''
    
    output = syncthing_adapter.connect()
    click.echo("%s" % output)
"""

#@click.group(invoke_without_command=True)
#@click.option('-v', '--version', is_flag=True, help='Print version information and quit')
#click.echo("%s '%s' is not a valid command." % ('kodedrive:', arg))
#click.echo("See 'kodedrive --help'.")

