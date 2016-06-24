import click
import cde_syncthing

@click.command()
@click.option('--as-cowboy', '-c', is_flag=True, help='Greet as a cowboy.')
@click.argument('arg', default='status', required=False)

def main(arg, as_cowboy):
	
	handler = {
		'start' : cde_syncthing.start,
		'stop' : cde_syncthing.stop,
		'inspect' : cde_syncthing.config,
		'status' : cde_syncthing.status,
		'name' : cde_syncthing.name
	}.get(arg, None)
	
	if handler:
		output = handler()
		output = output.strip()
		click.echo("%s" % output)
	else:
		click.echo("%s '%s' is not a valid command." % ('kodedrive:', arg))
		click.echo("See 'kodedrive --help'.")


