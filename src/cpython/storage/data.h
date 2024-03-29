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

extern PyTypeObject ArcType;
extern PyTypeObject BoxType;
extern PyTypeObject CircleType;
extern PyTypeObject ComponentType;
extern PyTypeObject LineType;
extern PyTypeObject NetType;
extern PyTypeObject PathType;
extern PyTypeObject PictureType;
extern PyTypeObject TextType;
extern PyTypeObject LineAttrType;
extern PyTypeObject FillAttrType;

PyObject *construct_arc(const struct xornsch_arc *data);
PyObject *construct_box(const struct xornsch_box *data);
PyObject *construct_circle(const struct xornsch_circle *data);
PyObject *construct_component(const struct xornsch_component *data);
PyObject *construct_line(const struct xornsch_line *data);
PyObject *construct_net(const struct xornsch_net *data);
PyObject *construct_path(const struct xornsch_path *data);
PyObject *construct_picture(const struct xornsch_picture *data);
PyObject *construct_text(const struct xornsch_text *data);
PyObject *construct_line_attr(const struct xornsch_line_attr *data);
PyObject *construct_fill_attr(const struct xornsch_fill_attr *data);

typedef struct {
	PyObject_HEAD
	struct xornsch_arc data;
	PyObject *line;
} Arc;

typedef struct {
	PyObject_HEAD
	struct xornsch_box data;
	PyObject *line;
	PyObject *fill;
} Box;

typedef struct {
	PyObject_HEAD
	struct xornsch_circle data;
	PyObject *line;
	PyObject *fill;
} Circle;

typedef struct {
	PyObject_HEAD
	struct xornsch_component data;
} Component;

typedef struct {
	PyObject_HEAD
	struct xornsch_line data;
	PyObject *line;
} Line;

typedef struct {
	PyObject_HEAD
	struct xornsch_net data;
} Net;

typedef struct {
	PyObject_HEAD
	struct xornsch_path data;
	PyObject *pathdata;
	PyObject *line;
	PyObject *fill;
} Path;

typedef struct {
	PyObject_HEAD
	struct xornsch_picture data;
} Picture;

typedef struct {
	PyObject_HEAD
	struct xornsch_text data;
	PyObject *text;
} Text;

typedef struct {
	PyObject_HEAD
	struct xornsch_line_attr data;
} LineAttr;

typedef struct {
	PyObject_HEAD
	struct xornsch_fill_attr data;
} FillAttr;

void prepare_arc(Arc *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_box(Box *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_circle(Circle *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_component(Component *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_line(Line *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_net(Net *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_path(Path *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_picture(Picture *self,
	xorn_obtype_t *type_return, const void **data_return);
void prepare_text(Text *self,
	xorn_obtype_t *type_return, const void **data_return);

#endif
