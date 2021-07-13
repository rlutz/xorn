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

import xorn.storage
import gc

class DelStatus:
    def __init__(self):
        self.exists = False

class DelWatcher:
    def __init__(self, status):
        self.status = status
        self.status.exists = True

    def __del__(self):
        self.status.exists = False

def collect(n):
    for i in xrange(n):
        gc.collect()

# component

status0 = DelStatus()
status1 = DelStatus()
collect(1)
assert status0.exists == False
assert status1.exists == False

component_data = xorn.storage.Component(symbol = DelWatcher(status0))
collect(1)
assert status0.exists == True
assert status1.exists == False

component_data.symbol = DelWatcher(status1)
collect(1)
assert status0.exists == False
assert status1.exists == True

del component_data
collect(1)
assert status0.exists == False
assert status1.exists == False

# picture

status0 = DelStatus()
status1 = DelStatus()
collect(1)
assert status0.exists == False
assert status1.exists == False

picture_data = xorn.storage.Picture(pixmap = DelWatcher(status0))
collect(1)
assert status0.exists == True
assert status1.exists == False

picture_data.pixmap = DelWatcher(status1)
collect(1)
assert status0.exists == False
assert status1.exists == True

del picture_data
collect(1)
assert status0.exists == False
assert status1.exists == False

# revision deleted

rev = xorn.storage.Revision()
status = DelStatus()
ob = rev.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

del rev
collect(2)
assert status.exists == False

# revision deleted (multiple revisions)

rev0 = xorn.storage.Revision()
status = DelStatus()
ob = rev0.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

rev1 = xorn.storage.Revision(rev0)
assert rev1 is not None
assert rev1 != rev0
del rev0
collect(2)
assert status.exists == True
del rev1
collect(2)
assert status.exists == False

# object overwritten

rev = xorn.storage.Revision()
status = DelStatus()
ob = rev.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

rev.set_object_data(ob, xorn.storage.Component())
collect(2)
assert status.exists == False
del rev
collect(2)
assert status.exists == False

# object overwritten (multiple revisions)

rev0 = xorn.storage.Revision()
status = DelStatus()
ob = rev0.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

rev1 = xorn.storage.Revision(rev0)
assert rev1 != rev0
rev1.set_object_data(ob, xorn.storage.Component())
collect(2)
assert status.exists == True
del rev0
collect(2)
assert status.exists == False
del rev1
collect(2)
assert status.exists == False

# object deleted

rev = xorn.storage.Revision()
status = DelStatus()
ob = rev.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

rev.delete_object(ob)
collect(2)
assert status.exists == False
del rev
collect(2)
assert status.exists == False

# object copied

rev0 = xorn.storage.Revision()
status = DelStatus()
ob = rev0.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

rev1 = xorn.storage.Revision()
rev1.copy_object(rev0, ob)
collect(2)
assert status.exists == True
del rev0
collect(2)
assert status.exists == True
del rev1
collect(2)
assert status.exists == False

# objected passed through revision

rev = xorn.storage.Revision()
status = DelStatus()
ob = rev.add_object(xorn.storage.Component(symbol = DelWatcher(status)))
assert ob is not None
collect(2)
assert status.exists == True

data = rev.get_object_data(ob)
del rev
collect(2)
assert status.exists == True
del data
collect(2)
assert status.exists == False
