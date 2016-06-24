import click
import cde_syncthing

@click.command()
@click.option('--as-cowboy', '-c', is_flag=True, help='Greet as a cowboy.')
@click.argument('arg', default='config', required=False)

def main(arg, as_cowboy):
	"""test"""

	greet = 'Howdy' if as_cowboy else 'Hello'

	#click.echo('{0}, {1}.'.format(greet, name))
	#click.echo('{0}, {1}.'.format(greet, syncthing_facade.config()))
	#click.echo('{0}, {1}.'.format(greet, syncthing_facade.start()))

	handler = {
		'start' : cde_syncthing.start,
		'stop' : cde_syncthing.stop,
		'config' : cde_syncthing.config
	}.get(arg, None)
	
	if handler:
	        output = handler()
	        output = output.strip()
		click.echo("%s" % output)


