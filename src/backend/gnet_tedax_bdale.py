# gnet_tedax_bdale.py - tEDAx gnetlist backend
# Copyright (C) 2018 Bdale Garbee
# Copyright (C) 2019 Roland Lutz
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

# --------------------------------------------------------------------------
# The tEDAx format is documented at http://repo.hu/projects/tedax/
# --------------------------------------------------------------------------

def run(f, netlist):
    f.write('tEDAx v1\n')
    f.write('begin netlist v1 netlist\n')
    f.write('\n')

    for package in netlist.packages:
        f.write('\tfootprint %s %s\n' % (
            package.refdes, package.get_attribute('footprint', 'UNKNOWN')))
        f.write('\tdevice %s %s\n' % (
            package.refdes, package.get_attribute('device', 'unknown')))
        f.write('\tvalue %s %s\n' % (
            package.refdes, package.get_attribute('value', '')))
        f.write('\n')

    for net in netlist.nets:
        for pin in net.connections:
            f.write('\tconn %s %s %s\n' % (
                net.name, pin.package.refdes, pin.number))
        f.write('\n')

    f.write('end netlist\n')
