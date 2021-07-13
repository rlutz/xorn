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

import types, xorn.storage

assert type(xorn) == types.ModuleType
assert type(xorn.storage) == types.ModuleType

mod_attrs = {
    'Revision': type,
    'Object': type,
    'Selection': type,

    'Arc': type,
    'Box': type,
    'Circle': type,
    'Component': type,
    'Line': type,
    'Net': type,
    'Path': type,
    'Picture': type,
    'Text': type,
    'LineAttr': type,
    'FillAttr': type,

    'get_objects_attached_to': types.FunctionType,
    'get_selected_objects': types.FunctionType,
    'get_added_objects': types.FunctionType,
    'get_removed_objects': types.FunctionType,
    'get_modified_objects': types.FunctionType,

    'select_none': types.FunctionType,
    'select_object': types.FunctionType,
    'select_attached_to': types.FunctionType,
    'select_all': types.FunctionType,
    'select_all_except': types.FunctionType,
    'select_including': types.FunctionType,
    'select_excluding': types.FunctionType,
    'select_union': types.FunctionType,
    'select_intersection': types.FunctionType,
    'select_difference': types.FunctionType,
    'selection_is_empty': types.FunctionType,
    'object_is_selected': types.FunctionType,
}

a = mod_attrs.keys()
a.sort()
b = [name for name in dir(xorn.storage) if not name.startswith('_')]
b.sort()
assert a == b
del a, b

for name in mod_attrs:
    assert type(xorn.storage.__dict__[name]) == mod_attrs[name]

def assert_attributes(ob, attrs):
    a = attrs.keys()
    b = [name for name in dir(ob) if not name.startswith('_')]
    a.sort()
    b.sort()
    assert a == b

    for attr in attrs:
        assert type(ob.__getattribute__(attr)) == attrs[attr]

assert_attributes(xorn.storage.Revision(), {
        'is_transient': types.MethodType,
        'finalize': types.MethodType,
        'transient': bool,

        'get_objects': types.MethodType,
        'object_exists': types.MethodType,
        'get_object_data': types.MethodType,
        'get_object_location': types.MethodType,

        'add_object': types.MethodType,
        'set_object_data': types.MethodType,
        'relocate_object': types.MethodType,
        'copy_object': types.MethodType,
        'copy_objects': types.MethodType,
        'delete_object': types.MethodType,
        'delete_objects': types.MethodType,
})

assert_attributes(xorn.storage.Arc(), {
        'x': float,
        'y': float,
        'radius': float,
        'startangle': int,
        'sweepangle': int,
        'color': int,
        'line': xorn.storage.LineAttr,
})
assert_attributes(xorn.storage.Box(), {
        'x': float,
        'y': float,
        'width': float,
        'height': float,
        'color': int,
        'line': xorn.storage.LineAttr,
        'fill': xorn.storage.FillAttr,
})
assert_attributes(xorn.storage.Circle(), {
        'x': float,
        'y': float,
        'radius': float,
        'color': int,
        'line': xorn.storage.LineAttr,
        'fill': xorn.storage.FillAttr,
})
assert_attributes(xorn.storage.Component(symbol = None), {
        'x': float,
        'y': float,
        'selectable': bool,
        'angle': int,
        'mirror': bool,
        'symbol': types.NoneType,
})
assert_attributes(xorn.storage.Line(), {
        'x': float,
        'y': float,
        'width': float,
        'height': float,
        'color': int,
        'line': xorn.storage.LineAttr,
})
assert_attributes(xorn.storage.Net(), {
        'x': float,
        'y': float,
        'width': float,
        'height': float,
        'color': int,
        'is_bus': bool,
        'is_pin': bool,
        'is_inverted': bool,
})
assert_attributes(xorn.storage.Path(), {
        'pathdata': str,
        'color': int,
        'line': xorn.storage.LineAttr,
        'fill': xorn.storage.FillAttr,
})
assert_attributes(xorn.storage.Picture(pixmap = None), {
        'x': float,
        'y': float,
        'width': float,
        'height': float,
        'angle': int,
        'mirror': bool,
        'pixmap': types.NoneType,
})
assert_attributes(xorn.storage.Text(), {
        'x': float,
        'y': float,
        'color': int,
        'text_size': int,
        'visibility': bool,
        'show_name_value': int,
        'angle': int,
        'alignment': int,
        'text': str,
})
assert_attributes(xorn.storage.LineAttr(), {
        'width': float,
        'cap_style': int,
        'dash_style': int,
        'dash_length': float,
        'dash_space': float,
})
assert_attributes(xorn.storage.FillAttr(), {
        'type': int,
        'width': float,
        'angle0': int,
        'pitch0': float,
        'angle1': int,
        'pitch1': float,
})
