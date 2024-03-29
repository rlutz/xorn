# Copyright (C) 2013-2021 Roland Lutz
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import xorn.guile

## [guile]
def add(x, y):
    return x + y

xorn.guile.define('add', add)
xorn.guile.eval_string('(add 1 2)')      # => 3
xorn.guile.eval_string('(add 1.0 2.0)')  # => 3.0
## [guile]

assert xorn.guile.eval_string('(add 1 2)') == 3
assert xorn.guile.eval_string('(add 1.0 2.0)') == 3.0

assert type(xorn.guile.eval_string('(add 1 2)')) == int
assert type(xorn.guile.eval_string('(add 1.0 2.0)')) == float
