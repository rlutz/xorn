/* Copyright (C) 2013 Roland Lutz

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2, or (at your option)
   any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.  */

#include "setup.h"


int main()
{
	xorn_file_t file;
	xorn_revision_t rev0, rev1, rev2, rev3;
	xorn_object_t ob0, ob1a, ob1b;

	setup(&file, &rev0, &rev1, &rev2, &rev3, &ob0, &ob1a, &ob1b);

	assert(xorn_object_exists_in_revision(rev0, ob0) == false);
	assert(xorn_object_exists_in_revision(rev0, ob1a) == false);
	assert(xorn_object_exists_in_revision(rev0, ob1b) == false);

	assert(xorn_object_exists_in_revision(rev1, ob0) == true);
	assert(xorn_object_exists_in_revision(rev1, ob1a) == false);
	assert(xorn_object_exists_in_revision(rev1, ob1b) == false);

	assert(xorn_object_exists_in_revision(rev2, ob0) == true);
	assert(xorn_object_exists_in_revision(rev2, ob1a) == true);
	assert(xorn_object_exists_in_revision(rev2, ob1b) == true);

	assert(xorn_object_exists_in_revision(rev3, ob0) == true);
	assert(xorn_object_exists_in_revision(rev3, ob1a) == false);
	assert(xorn_object_exists_in_revision(rev3, ob1b) == true);

	xorn_close_file(file);
	return 0;
}