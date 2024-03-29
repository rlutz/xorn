m4_divert(`-1')
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

m4_define(`stdout_diversion', `0')
m4_define(`structdef_diversion', `1')

# automatically undiverted
m4_define(`typeobs_diversion', `2')
m4_define(`construct_diversion', `3')
m4_define(`structdefs_diversion', `4')
m4_define(`prepare_diversion', `5')
m4_define(`endif_diversion', `6')

m4_define(`begin_divert', `m4_divert($1_diversion)m4_dnl')
m4_define(`end_divert', `m4_divert(`-1')')

m4_define(`undivert', `m4_undivert($1_diversion)m4_dnl')

m4_define(`Class', `m4_ifelse(`$#', `0', `_Class', `_Class`'_$1')')
m4_define(`cg_this_is',
  `m4_define(`typename', ``$1'')m4_define(`_Class', ``$2'')')

m4_define(`cg_pos', `')
m4_define(`cg_size', `')
m4_define(`cg_int', `')
m4_define(`cg_double', `')
m4_define(`cg_bool', `')

m4_define(`cg_string', `
  m4_define(`is_complex')
begin_divert(`structdef')
	PyObject *`$1';
end_divert
')

m4_define(`cg_line', `
  m4_define(`is_complex')
begin_divert(`structdef')
	PyObject *line;
end_divert
')

m4_define(`cg_fill', `
  m4_define(`is_complex')
begin_divert(`structdef')
	PyObject *fill;
end_divert
')

# ----------------------------------------------------------------------------

begin_divert(`stdout')
/* Copyright (C) 2013-2021 Roland Lutz

   THIS FILE IS AUTOMATICALLY GENERATED -- DO NOT EDIT

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.  */

#ifndef XORN_STORAGE_DATA_H
#define XORN_STORAGE_DATA_H

#include <Python.h>
#include "xornstorage.h"
end_divert
begin_divert(`typeobs')

end_divert
begin_divert(`construct')

end_divert
begin_divert(`prepare')

end_divert
begin_divert(`endif')

#endif
end_divert

# ----------------------------------------------------------------------------

m4_define(`cg_output', `
begin_divert(`typeobs')
extern PyTypeObject Class`'Type;
end_divert
begin_divert(`construct')
PyObject *construct_`'typename`'(const struct xornsch_`'typename *data);
end_divert
begin_divert(`structdefs')

typedef struct {
	PyObject_HEAD
	struct xornsch_`'typename data;
undivert(`structdef')
} Class;
end_divert

m4_ifelse(m4_index(typename, `_attr'), `-1',
	  `begin_divert(`prepare')')`'m4_dnl
void prepare_`'typename`'(Class *self,
	xorn_obtype_t *type_return, const void **data_return);
m4_ifelse(m4_index(typename, `_attr'), `-1',
	  `end_divert')`'m4_dnl
')
