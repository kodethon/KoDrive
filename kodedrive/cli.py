import click
import cde_syncthing

#@click.group(invoke_without_command=True)
#@click.option('-v', '--version', is_flag=True, help='Print version information and quit')
#click.echo("%s '%s' is not a valid command." % ('kodedrive:', arg))
#click.echo("See 'kodedrive --help'.")

@click.version_option()
@click.group(
    epilog="Run 'kodedrive COMMAND --help' for more information on a command.", 
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

    output = cde_syncthing.start()
    click.echo("%s" % output)

@cli.command()
def stop():
    ''' Stop KodeDrive daemon. '''

    output = cde_syncthing.stop()
    output = output.strip()
    click.echo("%s" % output)

@cli.command()
def inspect():
    ''' Return low-level information. '''

    output = cde_syncthing.config()
    click.echo("%s" % output)

@cli.command()
def status():
    ''' Determine if KodeDrive is up. '''

    output = cde_syncthing.status()
    click.echo("%s" % output)

@cli.command()
def name():
    ''' Display Kodedrive key. '''

    output = cde_syncthing.name()
    click.echo("%s" % output)

cli()
