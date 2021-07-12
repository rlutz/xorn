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

AM_CFLAGS = -Wall -Wextra

pkgpyexec_LTLIBRARIES = guile.la
guile_la_SOURCES = \
	module.c \
	module.h \
	proc.c \
	py2scm.c \
	scm2py.c
guile_la_CFLAGS = $(PYTHON_CFLAGS) $(GUILE_CFLAGS) $(AM_CFLAGS) \
		  -Wno-unused-parameter \
		  -Wno-missing-field-initializers \
		  $(Wno_cast_function_type_IF_SUPPORTED) \
		  -fno-strict-aliasing
guile_la_LDFLAGS = $(PYTHON_LDFLAGS) -module -avoid-version \
		   -export-symbols-regex '^initguile$$'
guile_la_LIBADD = $(GUILE_LIBS)

all-local: $(LTLIBRARIES)
	@if test "guile$(PYTHON_EXT_SUFFIX)" != guile.so; then \
	  rm -f ".libs/guile$(PYTHON_EXT_SUFFIX)"; \
	  $(LN_S) guile.so \
	          ".libs/guile$(PYTHON_EXT_SUFFIX)"; \
	fi

install-exec-local: installdirs
	@$(NORMAL_INSTALL)
	if test "guile$(PYTHON_EXT_SUFFIX)" != guile.so; then \
	  rm -f "$(DESTDIR)$(pkgpyexecdir)/guile$(PYTHON_EXT_SUFFIX)"; \
	  $(LN_S) guile.so \
	          "$(DESTDIR)$(pkgpyexecdir)/guile$(PYTHON_EXT_SUFFIX)"; \
	fi

uninstall-local:
	@$(NORMAL_UNINSTALL)
	if test "guile$(PYTHON_EXT_SUFFIX)" != guile.so; then \
	  rm -f "$(DESTDIR)$(pkgpyexecdir)/guile$(PYTHON_EXT_SUFFIX)"; \
	fi
