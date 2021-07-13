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

## \file xorn/guile.py
## Python wrapper for the CFFI library \c xorn._guile
#
# This file contains the low-level detail that connects Python code
# via CFFI with Guile.

## \namespace xorn.guile
## Embedding a Guile interpreter.
#
# This module allows embedding a Guile interpreter into a Python
# application.  It translates Python objects transparently into Guile
# objects and vice versa.  In order to make a Python function
# available to Guile code, just bind it to a variable name:
#
# \snippet guile.py guile

import sys
from xorn._guile import ffi as _ffi
from xorn._guile import lib as _lib

_TO_BOOL = { 0: False, 1: True }

_callables = {}

# When hacking this module, please note:
# - most Guile functions can only be called from within the interpreter
# - Python exceptions can only be raised from OUTSIDE the interpreter,
#   unless they are caught from within (like with _scm2py / _py2scm)


## Raised on Guile-related errors.

class GuileError(Exception):
    pass


def _call_guile(cb_fun, *args):
    l = [args, None, False, None]  # args, retval, success, exc_info
    h = _ffi.new_handle(l)
    _lib.scm_with_guile(cb_fun, h)
    if l[3] is not None:
        exc_type, exc_value, exc_traceback = l[3]
        l[3] = None  # avoid circular reference
        raise exc_type, exc_value, exc_traceback
    if not l[2]:
        raise GuileError
    return l[1]


## Return the variable bound to a symbol.
#
# Signals an error if there is no such binding or the symbol is not
# bound to a variable.

def lookup(name):
    return _call_guile(_lib._lookup_cb, name)

@_ffi.def_extern()
def _lookup_cb(h):
    l = _ffi.from_handle(h)
    name, = l[0]
    y = _lib.scm_variable_ref(_lib.scm_c_lookup(name))
    l[2] = True
    try:
        l[1] = _scm2py(y)
    except TypeError:
        l[3] = sys.exc_info()
    return _ffi.NULL


## Create a top level variable.
#
# If the named variable already exists, just changes its value.
#
# \throws GuileError if \a value can't be represented as a Guile
#                    object

def define(name, value):
    _call_guile(_lib._define_cb, name, value)

@_ffi.def_extern()
def _define_cb(h):
    l = _ffi.from_handle(h)
    name, value = l[0]
    try:
        x = _py2scm(value)
    except TypeError:
        l[3] = sys.exc_info()
    else:
        _lib.scm_c_define(name, x)
        l[2] = True
    return _ffi.NULL


## Load a file and evaluate its contents in the top-level environment.
#
# \a name must either be a full pathname or be a pathname relative to
# the current directory.  If the Guile variable \c %%load-hook is
# defined, the procedure to which it is bound will be called before
# any code is loaded.
#
# \sa [Guile documentation for %%load-hook](https://www.gnu.org/
#software/guile/manual/html_node/Loading.html#index-_0025load_002dhook)

def load(name):
    return _call_guile(_lib._load_cb, str(name))

@_ffi.def_extern()
def _load_cb(h):
    l = _ffi.from_handle(h)
    name, = l[0]
    y = _lib.scm_eval(
            _lib.scm_list_2(
                _lib.scm_from_utf8_symbol('load'),
                _lib.scm_from_utf8_stringn(name, len(name))),
            _lib.scm_current_module())
    l[2] = True
    try:
        l[1] = _scm2py(y)
    except TypeError:
        l[3] = sys.exc_info()
    return _ffi.NULL


## Parse a string as Scheme and evaluate the expressions it contains,
## in order, returning the last expression.

def eval_string(string):
    return _call_guile(_lib._eval_string_cb, string)

@_ffi.def_extern()
def _eval_string_cb(h):
    l = _ffi.from_handle(h)
    s, = l[0]
    y = _lib.scm_eval_string(_lib.scm_from_utf8_stringn(s, len(s)))
    l[2] = True
    try:
        l[1] = _scm2py(y)
    except TypeError:
        l[3] = sys.exc_info()
    return _ffi.NULL


################################################################################

@_ffi.def_extern()
def _scm2py_call_cb(h):
    l = _ffi.from_handle(h)
    proc, args = l[0]
    try:
        x = _py2scm(args)
    except TypeError:
        l[3] = sys.exc_info()
    else:
        y = _lib.scm_apply(proc, x, _lib.SCM_EOL)
        l[2] = True
        try:
            l[1] = _scm2py(y)
        except TypeError:
            l[3] = sys.exc_info()
    return _ffi.NULL

## Guile procedure.
#
# This type can't be directly instantiated.

class Procedure(object):
    # called from within the interpreter
    def __init__(self, proc):
        self._proc = proc

        # get string repr while we're within the interpreter
        self._str = _scm2py_string(
                        _lib.scm_simple_format(
                            _lib.SCM_BOOL_F,
                            _lib.scm_from_utf8_string('~S'),
                            _lib.scm_list_1(self._proc)))

    def __repr__(self):
        if not self._str.startswith('#<'):
            raise SystemError, \
                'Invalid procedure representation returned by Guile'
        return '<Guile ' + self._str[2:]

    def __call__(self, *args):
        return _call_guile(_lib._scm2py_call_cb, self._proc, args)

    def __eq__(self, other):
        return _TO_BOOL[_lib.scm_is_eq(self._proc, other._proc)]
    def __ne__(self, other):
        return not _TO_BOOL[_lib.scm_is_eq(self._proc, other._proc)]

    def __lt__(self, other):
        return NotImplemented
    def __le__(self, other):
        return NotImplemented
    def __gt__(self, other):
        return NotImplemented
    def __ge__(self, other):
        return NotImplemented

################################################################################

# called from within the interpreter
def _scm2py_string(x):
    p_len = _ffi.new('size_t *')
    buf = _lib.scm_to_utf8_stringn(x, p_len)
    s = _ffi.unpack(buf, p_len[0])
    _lib.free(buf)
    return s.decode('utf-8')

# called from within the interpreter, but may raise TypeError
def _scm2py(value):
    if _lib.scm_is_eq(value, _lib.SCM_UNSPECIFIED):
        return None
    if _lib.scm_is_exact_integer(value):
        return _lib.scm_to_int64(value)
    if _lib.scm_is_real(value):
        return _lib.scm_to_double(value)
    if _lib.scm_is_bool(value):
        return _TO_BOOL[_lib.scm_to_bool(value)]
    if _lib.scm_is_null(value):
        return ()
    if _lib.scm_is_string(value):
        return _scm2py_string(value)
    if _lib.scm_to_bool(_lib.scm_list_p(value)):
        l = _lib.scm_to_uint64(_lib.scm_length(value))
        result = []
        #_lib.scm_dynwind_begin(0)
        #_lib.scm_dynwind_unwind_handler(
        #    (void (*)(void *))Py_DecRef, result, 0)
        for i in xrange(l):
            result.append(_scm2py(_lib.scm_car(value)))
            value = _lib.scm_cdr(value)
        #_lib.scm_dynwind_end()
        return tuple(result)
    if _lib.scm_to_bool(_lib.scm_procedure_p(value)):
        name = _scm2py_string(_lib.scm_symbol_to_string(
                   _lib.scm_procedure_name(value)))
        try:
            return _callables[name]
        except KeyError:
            return Procedure(value)

    raise TypeError(
        _scm2py_string(
            _lib.scm_simple_format(
                _lib.SCM_BOOL_F,
                _lib.scm_from_utf8_string('Guile expression "~S" doesn\'t '
                                          'have a corresponding Python value'),
                _lib.scm_list_1(value))))

################################################################################

# called from within the interpreter
def _py2scm_exception(exc_type, exc_value, exc_traceback):
    try:
        tail = _py2scm(exc_value.args)
        args = _lib.scm_cons(
            _lib.scm_from_locale_string(exc_type.__name__), tail)
    except:
        exc_value_repr = repr(exc_value)
        args = _lib.scm_list_1(
            _lib.scm_from_locale_stringn(exc_value_repr, len(exc_value_repr)))

    _lib.scm_throw(_lib.scm_from_utf8_symbol('python-exception'), args)

    sys.stderr.write('*** scm_throw shouldn\'t have returned ***\n')
    return _lib.SCM_UNSPECIFIED

# called from OUTSIDE the interpreter
@_ffi.def_extern()
def _py2scm_call_cb(h):
    l = _ffi.from_handle(h)
    fun, args = l[0]
    try:
        l[1] = fun(*args)
    except:
        l[3] = sys.exc_info()
    return _ffi.NULL

# called from within the interpreter
def _py2scm_type_error():
    _lib.scm_error(_lib.scm_from_utf8_symbol('misc-error'), _ffi.NULL,
                   sys.exc_info()[1].message.encode('utf-8'),
                   _lib.SCM_EOL, _lib.SCM_BOOL_F)

    sys.stderr.write('*** scm_error shouldn\'t have returned ***\n')
    return _lib.SCM_UNSPECIFIED

@_ffi.def_extern()
def _py2scm_call_gsubr(args_scm):
    name = _scm2py_string(
        _lib.scm_symbol_to_string(
            _lib.scm_frame_procedure_name(
                _lib.scm_stack_ref(
                    _lib.scm_make_stack(_lib.SCM_BOOL_T, _lib.SCM_EOL),
                    _lib.scm_from_int64(0)))))
    fun = _callables[name]

    #_lib.scm_dynwind_begin(0)

    try:
        args = _scm2py(args_scm)
    except TypeError:
        return _py2scm_type_error()

    #_lib.scm_dynwind_py_decref(args)

    l = [(fun, args), None, False, None]
    h = _ffi.new_handle(l)
    _lib.scm_without_guile(_lib._py2scm_call_cb, h)
    if l[3] is not None:
        exc_info = l[3]
        l[3] = None  # avoid circular reference
        return _py2scm_exception(*exc_info)
    #_lib.scm_dynwind_py_decref(py_result)

    try:
        result_scm = _py2scm(l[1])
    except TypeError:
        return _py2scm_type_error()
    #_lib.scm_dynwind_end()
    return result_scm

# called from within the interpreter, but may raise TypeError
def _py2scm(value):
    if value is None:
        return _lib.SCM_UNSPECIFIED
    if value is False:
        return _lib.SCM_BOOL_F
    if value is True:
        return _lib.SCM_BOOL_T
    if type(value) == int:
        return _lib.scm_from_int64(value)
    if type(value) == float:
        return _lib.scm_from_double(value)
    if type(value) == str:
        return _lib.scm_from_utf8_stringn(value, len(value))
    if type(value) == unicode:
        #_lib.scm_dynwind_begin(0)
        utf8_str = value.encode('utf-8')
        # TODO: Handle encoding errors
        #_lib.scm_dynwind_py_decref(utf8_str)
        result = _lib.scm_from_utf8_stringn(utf8_str, len(utf8_str))
        #_lib.scm_dynwind_end()
        return result
    if hasattr(value, '__getitem__') and type(value) != dict:
        i = len(value)
        r = _lib.SCM_EOL
        while i > 0:
            i -= 1
            item = value[i]
            r = _lib.scm_cons(_py2scm(item), r)
        return r
    if type(value) == Procedure:
        return value._proc
    if callable(value):
        name = '__py_callable_%x__' % id(value)
        gsubr = _lib.scm_c_make_gsubr(name, 0, 0, 1,
                                      _lib._py2scm_call_gsubr)
        name = _scm2py_string(_lib.scm_symbol_to_string(
                   _lib.scm_procedure_name(gsubr)))
        if name in _callables:
            sys.stderr.write('*** duplicate gsubr name [%s] ***\n' % name)
            return _lib.SCM_UNSPECIFIED

        _callables[name] = value
        return gsubr

    raise TypeError('Python type "%.50s" doesn\'t have a corresponding Guile '
                    'type' % type(value).__name__)
