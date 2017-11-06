"""
Command-line entry point for Craftr.
"""

import argparse
import sys
import textwrap
import path from './utils/path'
import {Session} from './core/session'

parser = argparse.ArgumentParser(add_help=False, description="""
  Craftr is a domain-independent build system implemented in Python.

  Note: What you see here is the combined help for the Craftr CLI and
  the currently selected build backend "{backend}".
""", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-h', '--help', action='store_true')
parser.add_argument('-p', '--projectdir', metavar='DIR', default='.')
parser.add_argument('-b', '--builddir', metavar='DIR')
parser.add_argument('-c', '--config', metavar='FILE')
parser.add_argument('-d', '--define', metavar='OPTION=VAL', action='append')
parser.add_argument('-B', '--backend', metavar='MODULE')


class MultiArgparserDuck(object):

  def __init__(self, parsers):
    self.parsers = parsers

  def add_argument(self, *args, **kwargs):
    for p in self.parsers:
      p.add_argument(*args, **kwargs)


def main():
  # Parse the arguments. They will be parsed again when the backend was
  # able to augment the options/
  args, unknown_args = parser.parse_known_args()

  # The builddir can not be the same as the projectdir.
  args.projectdir = path.canonical(args.projectdir)
  if args.projectdir == path.cwd() and not args.builddir:
    print('fatal: projectdir can not be current directory unless\n'
          '       an alternative builddir is specified.')
    return 1

  if not args.builddir:
    args.builddir = '.'

  # Default configuration is the `craftrconfig.toml` in the build
  # directory, or if that doesn't exist, from the cwd.
  if not args.config:
    config_filename = path.join(args.builddir, 'craftrconfig.toml')
    if not path.isfile(config_filename):
      config_filename = './craftrconfig.toml'
      if not path.isfile(config_filename):
        config_filename = None
    args.config = config_filename

  # Initialize our build session.
  session = Session(args.projectdir, args.builddir)
  if args.config:
    session.config.read(args.config)

  # Apply override configuration values from the command-line.
  for s in (args.define or ()):
    if '=' not in s:
      print('fatal: invalid -d, --define argument: {!r}'.format(s))
      return 1
    k, v = s.partition('=')[::2]
    if not v:
      session.config.pop(k, None)
    else:
      session.config[k] = v

  # Load the build backend.
  if args.backend:
    session.config['build.backend'] = args.backend
  args.backend = session.config.get('build.backend', 'default')
  try:
    backend = require.try_('./build_backends/' + args.backend, args.backend)
  except require.ResolveError:
    print('error: could not find module "{}"'.format(args.backend))
    if not args.help:
      raise
    args.backend = '<not-found:{}>'.format(args.backend)
  else:
    prog = parser.prog + ' <backend={}>'.format(args.backend)
    backend_parser = argparse.ArgumentParser(prog=prog)
    if hasattr(backend, 'build_argparser'):
      backend.build_argparser(MultiArgparserDuck([parser, backend_parser]))

  if args.help:
    parser.description = parser.description.format(backend=args.backend)
    parser.print_help()
    return 0

  backend_args = backend_parser.parse_args(unknown_args)

  # Find the build script as a Node.py module.
  filename = path.join(args.projectdir, './Craftrfile.py')
  module = require.new(session.projectdir).resolve(filename)

  # Enter the session context and execute the build backend.
  with session, require.context.push_main(module):
    return backend.build_main(backend_args, session, module)


if require.main == module:
  sys.exit(main())
