# The Craftr build system
# Copyright (C) 2016  Niklas Rosenstein
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

options = session.module.options
from craftr.loaders import external_archive

cURL = Framework('cURL',
  include = [],
  defines = [],
  libs = []
)

if platform.name == 'win':
  cURL['libs'] += ['Ws2_32', 'Wldap32']
else:
  error('platform currently not supported: {}'.format(platform.name))

source_directory = external_archive(
  "https://curl.haxx.se/download/curl-{}.tar.gz".format(options.version)
)
cURL['include'].append(path.join(source_directory, 'include'))

if options.static:
  cURL['defines'].append('CURL_STATICLIB')

load_module('craftr.lang.cxx.*')

libcURL = cxx_library(
  link_style = 'static' if options.static else 'shared',
  inputs = c_compile(
    sources = glob(['src/**/*.c', 'lib/**/*.c'], parent = source_directory),
    include = [path.join(source_directory, 'lib')],
    defines = ['BUILDING_LIBCURL'],
    frameworks = [cURL]
  ),
  output = 'cURL'
)

cxx_extend_framework(cURL, libcURL)
