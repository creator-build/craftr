
import argparse
from pathlib import Path

from craftr.core.context import Context
from craftr.core.settings import Settings

PYTHON_BUILD_SCRIPT = 'build.craftr.py'

parser = argparse.ArgumentParser()
parser.add_argument('-O', '--option', default=[], action='append',
  help='Set or override an option in the settings of the build.')
parser.add_argument('--settings-file', default=Context.CRAFTR_SETTINGS_FILE, type=Path,
  help='Point to another settings file. (default: %(default)s)')
parser.add_argument('tasks', metavar='task', nargs='*')


def main() -> None:
  args = parser.parse_args()
  settings = Settings.from_file(Path(args.settings_file))
  settings.update(Settings.parse(args.option))
  context = Context(settings)
  project = context.project(Path.cwd())

  filename = PYTHON_BUILD_SCRIPT
  scope = {'project': project, '__file__': filename, '__name__': '__main__'}
  exec(compile(Path(filename).read_text(), filename, 'exec'), scope, scope)

  context.execute(args.tasks or None)


if __name__ == '__main__':
  main()
