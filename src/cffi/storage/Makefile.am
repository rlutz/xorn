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

pkgpyexec_LTLIBRARIES = _storage.la
_storage_la_SOURCES = _storage.c
_storage_la_CPPFLAGS = -I$(top_srcdir)/include
_storage_la_CFLAGS = $(PYTHON_CFLAGS) $(AM_CFLAGS) \
		     -Wno-missing-field-initializers
_storage_la_LDFLAGS = $(PYTHON_LDFLAGS) -module -avoid-version
_storage_la_LIBADD = ../../storage/libxornstorage.la

${srcdir}/_storage.c: gen_ext.py cdef.h
	$(AM_V_GEN)$(PYTHON) $^ tmp-$$$$ >/dev/null && mv tmp-$$$$ $@

all-local: $(LTLIBRARIES)
	@if test "_storage$(PYTHON_EXT_SUFFIX)" != _storage.so; then \
	  rm -f ".libs/_storage$(PYTHON_EXT_SUFFIX)"; \
	  $(LN_S) _storage.so \
	          ".libs/_storage$(PYTHON_EXT_SUFFIX)"; \
	fi

install-exec-local: installdirs
	@$(NORMAL_INSTALL)
	if test "_storage$(PYTHON_EXT_SUFFIX)" != _storage.so; then \
	  rm -f "$(DESTDIR)$(pkgpyexecdir)/_storage$(PYTHON_EXT_SUFFIX)"; \
	  $(LN_S) _storage.so \
	          "$(DESTDIR)$(pkgpyexecdir)/_storage$(PYTHON_EXT_SUFFIX)"; \
	fi

uninstall-local:
	@$(NORMAL_UNINSTALL)
	if test "_storage$(PYTHON_EXT_SUFFIX)" != _storage.so; then \
	  rm -f "$(DESTDIR)$(pkgpyexecdir)/_storage$(PYTHON_EXT_SUFFIX)"; \
	fi

clean-local:
	rm -f tmp-*

EXTRA_DIST = gen_ext.py cdef.h

MAINTAINERCLEAN_FILES = _storage.c
