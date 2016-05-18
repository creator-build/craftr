# Copyright (C) 2016  Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import craftr
from craftr import path, shell, warn, session, Target
from craftr import __version__ as craftr_version
from craftr.utils import find_program

import json
import ninja_syntax
import re
import sys


def get_ninja_version():
  ''' Read the ninja version from the `ninja` program and return it. '''

  if not hasattr(get_ninja_version, 'result'):
    get_ninja_version.result = shell.pipe('ninja --version', shell=True).output.strip()
  return get_ninja_version.result


def validate_ident(name):
  ''' Raises a `ValueError` if *name* is not a valid Ninja identifier. '''

  if not re.match('[A-Za-z0-0_\.]+', name):
    raise ValueError('{0!r} is not a valid Ninja identifier'.format(name))


def export(fp, main_module, cache):
  ''' Writes the Ninja build definitions of the current session to *fp*. '''

  version = get_ninja_version()
  writer = ninja_syntax.Writer(fp, width=2 ** 16)
  writer.comment('this file was automatically generated by Craftr-{0}'.format(craftr_version))
  writer.comment('meta build file: {0}'.format(main_module.__file__))
  writer.comment('https://github.com/craftr-build/craftr')
  cache.write(writer)

  for key, value in session.var.items():
    writer.variable(key, value)
  writer.newline()

  default = []
  for target in sorted(session.targets.values(), key=lambda t: t.fullname):
    validate_ident(target.fullname)
    if target.pool:
      validate_ident(target.pool)
    if target.deps not in (None, 'gcc', 'msvc'):
      raise ValueError('Target({0}).deps = {1!r} is invalid'.format(target.fullname, target.deps))

    # On Windows, commands that are not executables require the interpreter.
    # See issue craftr-build/craftr#67
    command_args = target.command
    if sys.platform.startswith('win32'):
      try:
        prog = find_program(command_args[0])
      except FileNotFoundError:
        # do nothing and assume the file is executable
        warn('ninja export: program {0!r} (target: {1}) could not be found'.format(
          command_args[0], target.fullname))
      else:
        # xxx: do a more sophisticated check if the file is an executable image.
        is_executable = prog.lower().endswith('.exe')
        if not is_executable:
          command_args = ['cmd', '/c'] + command_args

    # Convert the command arguments to a command string.
    command = ' '.join(map(shell.quote, command_args))

    # Fix escaped $ variables on Unix, see issue craftr-build/craftr#30
    command = re.sub(r"'(\$\w+)'", r'\1', command)

    writer.rule(target.fullname, command, pool=target.pool, deps=target.deps,
      depfile=target.depfile, description=target.description)

    if target.msvc_deps_prefix:
      # We can not write msvc_deps_prefix on the rule level with Ninja 1.6.0
      # or older. Write it global instead, but that *could* lead to issues...
      indent = 1 if version > '1.6.0' else 0
      writer.variable('msvc_deps_prefix', target.msvc_deps_prefix, indent)

    inputs = path.normpath(target.inputs or [])
    outputs = path.normpath(target.outputs) if target.outputs is not None else [target.fullname]
    implicit_deps = path.normpath(target.implicit_deps) + [x.fullname for x in target.requires]
    if target.foreach:
      assert target.inputs is not None and target.outputs is not None
      assert len(inputs) == len(outputs)
      for infile, outfile in zip(inputs, outputs):
        writer.build(
          [path.normpath(outfile)],
          target.fullname,
          [path.normpath(infile)],
          implicit=implicit_deps,
          order_only=path.normpath(target.order_only_deps))
    else:
      writer.build(
        outputs,
        target.fullname,
        path.normpath(inputs),
        implicit=implicit_deps,
        order_only=path.normpath(target.order_only_deps))

    if target.fullname not in outputs:
      writer.build(target.fullname, 'phony', outputs)
    if not target.explicit:
      default.append(target.fullname)
    writer.newline()

  if default:
    writer.default(default)


class CraftrCache(object):
  ''' Represents the cached data in a Ninja manifest for Craftr.

  :param options: A list of options for the environment.
  :param targets: A dictionary of target names to dictionary
    of target information (currently only contains a key ``'rts'``
    that specifies if the target requires RTS or not).
  :param session: If passes and *targets* is None, generates
    the *targets* dictionary from the targets in the session.
  '''

  def __init__(self, options=None, path=None, targets=None, session=None):
    if targets is None and session:
      # Generate the targets data from the session.
      targets = {}
      for name, target in session.targets.items():
        targets[name] = {
          'rts': target.get_rts_mode(),
          'explicit': target.explicit,
        }

    self.options = options or []
    self.path = path or []
    self.targets = targets or {}

  def get_rts_mode(self, target_names):
    ''' Same as :meth:`Target.get_rts_mode()` only that it checks
    the cached data of the specified *target_names*.

    :param target_names: A list of target names. If the list is
      empty, checks all targets, however ignore targets that are
      not included by the default phony target.
    :return: Either of

      * :data:`Target.RTS_None`
      * :data:`Target.RTS_Mixed`
      * :data:`Target.RTS_Plain`
    '''

    explicit = True
    if not target_names:
      explicit = False
      target_names = self.targets.keys()

    mode = None
    for name in target_names:
      try:
        info = self.targets[name]
      except KeyError:
        continue
      if info['explicit'] and not explicit:
        # Ignore explicit targets if we're targeting the default phony.
        continue
      if mode is None or info['rts'] == Target.RTS_Mixed:
        mode = info['rts']
      elif mode != info['rts']:
        mode = Target.RTS_Mixed

    return mode or Target.RTS_None


  def write(self, writer):
    writer.comment('@craftr.options: ' + json.dumps(self.options))
    writer.comment('@craftr.path: ' + json.dumps(self.path))
    writer.comment('@craftr.targets: ' + json.dumps(self.targets))

  @staticmethod
  def read(filename=None):
    ''' Extracts the cached data encoded in the Ninja manifest
    required for Craftr when the execution phase is skipped.

    :param filename: The path to the Ninja manifest. Defaults
      to :data:`craftr.MANIFEST`.
    :return: :class:`CraftrCache` '''

    if not filename:
      filename = craftr.MANIFEST

    options = []
    path = []
    targets = {}
    with open(filename) as fp:
      # Go over each line and parse the cached data.
      for line in fp:
        if not line.startswith('#'):
          break
        line = line.lstrip('#').lstrip()
        if line.startswith('@craftr.options:'):
          options = json.loads(line[16:])
        elif line.startswith('@craftr.path:'):
          path = json.loads(line[13:])
        elif line.startswith('@craftr.targets:'):
          targets = json.loads(line[16:])

    return CraftrCache(options, path, targets)
