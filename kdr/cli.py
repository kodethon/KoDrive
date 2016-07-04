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
    help="Specify a folder.")

def ls(path):
    ''' List synchronized directories. '''
    
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
    	output = cli_syncthing_adapter.init(key, tag, path)
    	click.echo("%s" % output)

@main.command()
@click.argument(
	'path',
	type=click.Path(exists=True, writable=True, resolve_path=True), 
  nargs=1, metavar="PATH",
)
def unlink(**kwargs):
	''' Stop synchronization of directory. '''
	
	return

@main.command()
@click.argument(
	'path', nargs=1, 
	type=click.Path(exists=True, writable=True, resolve_path=True), 
)
def refresh(path):
  ''' Force synchronization of directory. '''

  output = cli_syncthing_adapter.refresh(path)
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
