# Copyright (C) 2015  Niklas Rosenstein
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

from craftr import session, path
from craftr.shell import quote, Process

import craftr
import ninja_syntax
import re


def get_ninja_version():
  if not hasattr(get_ninja_version, 'result'):
    get_ninja_version.result = Process(['ninja', '--version'], shell=True).stdout.strip()
  return get_ninja_version.result


def validate_ident(name):
  ''' Raises a `ValueError` if *name* is not a valid Ninja identifier. '''

  if not re.match('[A-Za-z0-0_\.]+', name):
    raise ValueError('{0!r} is not a valid Ninja identifier'.format(name))


def export(fp, main_module):
  ''' Writes the Ninja build definitions of the current session to *fp*. '''

  version = get_ninja_version()
  writer = ninja_syntax.Writer(fp, width=2 ** 16)
  writer.comment('this file was automatically generated by Craftr-{0}'.format(craftr.__version__))
  writer.comment('meta build file: {0}'.format(main_module.__file__))
  writer.comment('https://github.com/craftr-build/craftr')
  writer.newline()

  for key, value in session.var.items():
    writer.variable(key, value)
  writer.newline()

  default = []
  for target in sorted(session.targets.values(), key=lambda t: t.fullname):
    validate_ident(target.fullname)
    if target.pool:
      validate_ident(target.pool)
    if not target.inputs:
      continue
    if target.deps not in (None, 'gcc', 'msvc'):
      raise ValueError('Target({0}).deps = {1!r} is invalid'.format(target.fullname, target.deps))
    command = ' '.join(map(quote, target.command))
    command = re.sub(r"'(\$\w+)'", r'\1', command)  # Fix escaped $ variables on Unix, see issue #30

    writer.rule(target.fullname, command, pool=target.pool, deps=target.deps,
      depfile=target.depfile, description=target.description)

    if target.msvc_deps_prefix:
      # We can not write msvc_deps_prefix on the rule level with Ninja 1.6.0
      # or older. Write it global instead, but that *could* lead to issues...
      indent = 1 if version > '1.6.0' else 0
      writer.variable('msvc_deps_prefix', target.msvc_deps_prefix, indent)

    outputs = path.normpath(target.outputs) if target.outputs else [target.fullname]
    if target.foreach:
      assert len(target.inputs) == len(target.outputs)
      for infile, outfile in zip(target.inputs, target.outputs):
        writer.build(
          [path.normpath(outfile)],
          target.fullname,
          [path.normpath(infile)],
          implicit=path.normpath(target.implicit_deps),
          order_only=path.normpath(target.order_only_deps))
    else:
      writer.build(
        outputs,
        target.fullname,
        path.normpath(target.inputs),
        implicit=path.normpath(target.implicit_deps),
        order_only=path.normpath(target.order_only_deps))

    if target.outputs and target.fullname not in target.outputs:
      writer.build(target.fullname, 'phony', outputs)
    if target.pool != 'console':
      default.append(target.fullname)
    writer.newline()

  if default:
    writer.default(default)
