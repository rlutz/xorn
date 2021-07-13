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

## \file storage.py
## Python wrapper for the CFFI library \c xorn._storage
#
# This file contains the low-level detail that connects Python code
# with the CFFI storage library.  If you are trying to understand what
# the storage backend does, this probably won't get you very far; you
# may want to have a look at the header file \c xornstorage.h and/or
# the C implementation in \c src/storage/ instead.

## \namespace xorn.storage
## Xorn storage backend.
#
# Python extension providing access to the storage library.
#
# \sa \ref storage
# \sa xornstorage.h

"""Xorn storage backend"""

from xorn._storage import ffi as _ffi
from xorn._storage import lib as _lib


# internal definitions

_TO_BOOL = { 0: False, 1: True }

def _check_object_type(t, val, fname, arg_name, arg_ind):
    if t == float and type(val) == int:
        return
    if t == bool and val in [0, 1]:
        return
    if not isinstance(val, t):
        raise TypeError, \
            "%s() argument %d ('%s') must be %.50s, not %.50s" % (
                fname, arg_ind, arg_name, t.__name__, val.__class__.__name__)

## Data descriptor for Revision.transient.
class _TransientDescriptor(object):
    """Whether the revision can be changed."""

    def __get__(self, instance, owner):
        return instance.is_transient()

    def __set__(self, instance, value):
        if type(value) != bool:
            raise TypeError, "transient attribute must be bool"

        if not value:
            instance.finalize()
        elif not instance.is_transient():
            raise ValueError, "can't make revision transient again"

    def __delete__(self, instance):
        raise TypeError, "can't delete transient attribute"

class _RenameDescriptor(object):
    def __init__(self, *path):
        self.path = path

    def __get__(self, instance, owner):
        obj = instance._cdata
        for name in self.path:
            obj = getattr(obj, name)
        return obj

    def __set__(self, instance, value):
        obj = instance._cdata
        for name in self.path[:-1]:
            obj = getattr(obj, name)
        setattr(obj, self.path[-1], value)

class _StringDescriptor(object):
    def __init__(self, *path):
        self.path = path
        self.internal = '_s_' + '_'.join(self.path)

    def __get__(self, instance, owner):
        obj = instance._cdata
        for name in self.path:
            obj = getattr(obj, name)
        if obj.s == _ffi.NULL:
            return ''
        return _ffi.unpack(obj.s, obj.len)

    def __set__(self, instance, value):
        s = str(value) if type(value) != str else value
        l = len(s)
        if not l:
            buf = _ffi.NULL
        else:
            buf = _ffi.new('char[]', l)
            _ffi.memmove(buf, s, l)
        setattr(instance, self.internal, buf)

        obj = instance._cdata
        for name in self.path:
            obj = getattr(obj, name)
        obj.s = buf
        obj.len = l

_keepalive = {}

class _PointerHelper(object):
    def __init__(self, value):
        self.value = value
        self.handle = _ffi.new_handle(self)

@_ffi.def_extern()
def _incref_cb(ptr):
    p = _ffi.from_handle(ptr)
    try:
        _keepalive[p] += 1
    except KeyError:
        _keepalive[p] = 1

@_ffi.def_extern()
def _decref_cb(ptr):
    p = _ffi.from_handle(ptr)
    refcnt = _keepalive[p]
    if refcnt > 1:
        _keepalive[p] = refcnt - 1
    else:
        del _keepalive[p]

class _PointerDescriptor(object):
    def __init__(self, *path):
        self.path = path
        self.internal = '_p_' + '_'.join(self.path)

    def __get__(self, instance, owner):
        obj = instance._cdata
        for name in self.path:
            obj = getattr(obj, name)
        if obj.ptr == _ffi.NULL:
            return None
        p = _ffi.from_handle(obj.ptr)
        return p.value

    # BUG: This makes an object live forever.
    def __set__(self, instance, value):
        obj = instance._cdata
        for name in self.path:
            obj = getattr(obj, name)

        if value is None:
            setattr(instance, self.internal, None)
            obj.ptr = _ffi.NULL
            obj.incref = _ffi.NULL
            obj.decref = _ffi.NULL
        else:
            p = _PointerHelper(value)
            setattr(instance, self.internal, p)
            obj.ptr = p.handle
            obj.incref = _lib._incref_cb
            obj.decref = _lib._decref_cb

class _LineDescriptor(object):
    def __get__(self, instance, owner):
        l = instance._line
        if l is None:
            l = instance._line = LineAttr(_cdata = instance._cdata.line)
        return l

    def __set__(self, instance, value):
        if not isinstance(value, LineAttr):
            raise TypeError, \
                "value must be %.50s, not %.50s" % (
                    LineAttr.__name__, val.__class__.__name__)
        _ffi.memmove(_ffi.addressof(instance._cdata.line),
                     _ffi.addressof(value._cdata),
                     _ffi.sizeof(instance._cdata.line))

class _FillDescriptor(object):
    def __get__(self, instance, owner):
        l = instance._fill
        if l is None:
            l = instance._fill = FillAttr(_cdata = instance._cdata.fill)
        return l

    def __set__(self, instance, value):
        if not isinstance(value, FillAttr):
            raise TypeError, \
                "value must be %.50s, not %.50s" % (
                    FillAttr.__name__, val.__class__.__name__)
        _ffi.memmove(_ffi.addressof(instance._cdata.fill),
                     _ffi.addressof(value._cdata),
                     _ffi.sizeof(instance._cdata.fill))

def _copy_cdata(orig):
    pcopy = _ffi.new(_ffi.typeof(orig))
    _ffi.memmove(pcopy, orig, _ffi.sizeof(pcopy[0]))
    return pcopy[0]

## A particular state of the contents of a file.

class Revision(object):
    """A particular state of the contents of a file.

       Revision() -> new revision
       Revision(rev) -> copy of an existing revision

    """

    ## Whether the revision is transient.
    #
    # Reading and writing this is equivalent to calling \ref
    # is_transient and \ref finalize.  Cannot be changed from \c False
    # to \c True.

    transient = _TransientDescriptor()

    ## Create a new revision, either from scratch or by copying an
    ## existing one.
    #
    # \param rev %Revision to copy, or \c None.
    #
    # There is a slight difference between creating two empty
    # revisions and copying an empty one: only in the second case,
    # objects of one revision will be valid in the other.
    #
    # \throw MemoryError if there is not enough memory

    def __init__(self, rev = None):
        if rev is None:
            self._cdata = _lib.xorn_new_revision(_ffi.NULL)
        else:
            if not isinstance(rev, Revision):
                raise TypeError, \
                    "Revision() argument 1 ('rev') must be %.50s or None, " \
                    "not %.50s" % (Revision.__name__, rev.__class__.__name__)

            self._cdata = _lib.xorn_new_revision(rev._cdata)

        if self._cdata == _ffi.NULL:
            raise MemoryError

    def __del__(self):
        _lib.xorn_free_revision(self._cdata)

    ## Return whether a revision can be changed.
    #
    # When a revision is created, it is initially \a transient,
    # i.e. changeable.  This can be changed by calling \ref finalize.
    # After that, it can't be changed directly any more---you will
    # have to create a transient copy if you want to change it again.

    def is_transient(self):
        """rev.is_transient() -> bool -- whether the revision can be changed"""

        return _TO_BOOL[_lib.xorn_revision_is_transient(self._cdata)]

    ## Prevent further changes to a revision.
    #
    # When a revision is created, it is initially \a transient,
    # i.e. changeable.  However, it is typically not desired for a
    # revision to change once it is in its desired state.  Using this
    # function, you can prevent further changes to the revision.  It
    # will still be possible to create a copy of the revision and
    # change that.
    #
    # \return \c None

    def finalize(self):
        """rev.finalize() -- prevent further changes to the revision"""

        _lib.xorn_finalize_revision(self._cdata)

    ## Return a list of all objects in a revision.
    #
    # The objects are returned in their actual order.  Attached
    # objects are listed after the object they are attached to.
    #
    # \throw MemoryError if there is not enough memory
    #
    # Example:
    # \snippet storage_funcs.py get objects

    def get_objects(self):
        """rev.get_objects() -> [Object] --
           a list of all objects in the revision"""

        pobjects = _ffi.new('xorn_object_t **')
        pcount = _ffi.new('size_t *')

        if _lib.xorn_get_objects(self._cdata, pobjects, pcount) == -1:
            return MemoryError

        l = [Object(pobjects[0][i]) for i in xrange(pcount[0])]
        _lib.free(pobjects[0])
        return l

    ## Return whether an object exists in a revision.

    def object_exists(self, ob):
        """rev.object_exists(ob) -> bool --
           whether an object exists in the revision"""

        _check_object_type(Object, ob, 'Revision.object_exists', 'ob', 1)
        return _TO_BOOL[_lib.xorn_object_exists_in_revision(
                            self._cdata, ob._cdata)]

    ## Get the data of an object in a revision.
    #
    # Changing the returned data will not have an effect on the
    # object; use \ref set_object_data to change the object.
    #
    # \return Returns an instance of the appropriate data class.
    #
    # \throw KeyError    if \a ob doesn't exist in the revision
    # \throw ValueError  if the object type is not supported
    #                    (should not happen)
    # \throw MemoryError if there is not enough memory
    #
    # Example:
    # \snippet storage_funcs.py get/set object data

    def get_object_data(self, ob):
        """rev.get_object_data(ob) -> Arc/Box/... --
           get the data of an object"""

        _check_object_type(Object, ob, 'Revision.get_object_data', 'ob', 1)

        obtype = _lib.xorn_get_object_type(self._cdata, ob._cdata)
        if obtype == _lib.xorn_obtype_none:
            raise KeyError, "object does not exist"

        if obtype == _lib.xornsch_obtype_arc:
            return Arc(_cdata = _copy_cdata(
                _lib.xornsch_get_arc_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_box:
            return Box(_cdata = _copy_cdata(
                _lib.xornsch_get_box_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_circle:
            return Circle(_cdata = _copy_cdata(
                _lib.xornsch_get_circle_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_component:
            return Component(_cdata = _copy_cdata(
                _lib.xornsch_get_component_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_line:
            return Line(_cdata = _copy_cdata(
                _lib.xornsch_get_line_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_net:
            return Net(_cdata = _copy_cdata(
                _lib.xornsch_get_net_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_path:
            return Path(_cdata = _copy_cdata(
                _lib.xornsch_get_path_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_picture:
            return Picture(_cdata = _copy_cdata(
                _lib.xornsch_get_picture_data(self._cdata, ob._cdata)))
        if obtype == _lib.xornsch_obtype_text:
            return Text(_cdata = _copy_cdata(
                _lib.xornsch_get_text_data(self._cdata, ob._cdata)))

        raise ValueError, "object type not supported (%d)" % obtype

    ## Get the location of an object in the object structure.
    #
    # \return Returns a tuple <tt>(attached_to, pos)</tt> where \c
    # attached_to is the object to which \a ob is attached and \c pos
    # is the index of \a ob relative to its sibling objects.
    #
    # \throw KeyError if \a ob doesn't exist in the revision

    def get_object_location(self, ob):
        """rev.get_object_location(ob) -> Object, int --
           get the location of an object in the object structure"""

        _check_object_type(Object, ob, 'Revision.get_object_location', 'ob', 1)

        p_attached_to = _ffi.new('xorn_object_t *')
        p_attached_to[0] = _ffi.NULL
        p_position = _ffi.new('unsigned int *')
        p_position[0] = _ffi.cast('unsigned int', -1)

        if _lib.xorn_get_object_location(self._cdata, ob._cdata,
                                         p_attached_to, p_position) == -1:
            raise KeyError, "object does not exist"

        if p_attached_to[0] == _ffi.NULL:
            return None, p_position[0]
        else:
            return Object(p_attached_to[0]), p_position[0]

    ## Add a new object to a transient revision.
    #
    # The object is appended to the end of the object list.
    #
    # \a data must be an instance of one of the object data types
    # (Arc, Box, Circle, Component, Line, Net, Path, Picture, or Text).
    #
    # \return Returns the new object.
    #
    # \throw ValueError  if the revision isn't transient
    # \throw TypeError   if \a data doesn't have a valid type
    # \throw ValueError  if \a data contains an invalid value
    # \throw MemoryError if there is not enough memory
    #
    # Example:
    # \snippet storage_funcs.py add object

    def add_object(self, data):
        """rev.add_object(data) -> Object -- add a new object to the revision
           
           Only callable on a transient revision.
        """

        try:
            obtype = data._obtype
            cdata_ptr = _ffi.addressof(data._cdata)
        except AttributeError:
            raise TypeError, \
                "Revision.add_object() argument 'data' (pos 1) " \
                "must be of xorn.storage object type, not %.50s" \
                  % data.__class__.__name__

        perr = _ffi.new('xorn_error_t *')
        ob_cdata = _lib.xorn_add_object(self._cdata, obtype, cdata_ptr, perr)
        if ob_cdata != _ffi.NULL:
            return Object(ob_cdata)

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        if perr[0] == _lib.xorn_error_invalid_object_data:
            raise ValueError, "invalid object data"
        if perr[0] == _lib.xorn_error_out_of_memory:
            raise MemoryError
        if perr[0] == _lib.xorn_error_invalid_argument:
            raise SystemError, "error preparing object data"
        raise SystemError, "invalid Xorn error code"

    ## Set the data of an object in a transient revision.
    #
    # If the object does not exist in the revision, it is created and
    # appended to the end of the object list.
    #
    # \param ob   An object which has previously been returned by a Xorn
    #             function for either this revision, one of its
    #             ancestors, or a revision which has a common ancestor
    #             with it.
    #
    # \param data An instance of one of the object data types (Arc,
    #             Box, Circle, Component, Line, Net, Path, Picture, or
    #             Text).  The type may be different from the previous
    #             type of the object but must be Net or Component if
    #             there are objects attached to \a ob, and must be
    #             Text if \a ob itself is attached to an object.
    #
    # \return \c None
    #
    # \throw ValueError  if the revision isn't transient
    # \throw TypeError   if \a data doesn't have a valid type
    # \throw ValueError  if \a data contains an invalid value
    # \throw ValueError  if \a ob is attached to an object but the new
    #                    object type wouldn't permit attaching the object
    # \throw ValueError  if there are objects attached to \a ob but
    #                    the new object type wouldn't permit attaching
    #                    objects
    # \throw MemoryError if there is not enough memory
    #
    # Example:
    # \snippet storage_funcs.py get/set object data

    def set_object_data(self, ob, data):
        """rev.set_object_data(ob, data) -- set the data of an object
           
           Only callable on a transient revision.
        """

        _check_object_type(Object, ob, 'Revision.set_object_data', 'ob', 1)

        try:
            obtype = data._obtype
            cdata_ptr = _ffi.addressof(data._cdata)
        except AttributeError:
            raise TypeError, \
                "Revision.set_object_data() argument 'data' (pos 2) " \
                "must be of xorn.storage object type, not %.50s" \
                  % data.__class__.__name__

        perr = _ffi.new('xorn_error_t *')
        if _lib.xorn_set_object_data(self._cdata, ob._cdata,
                                     obtype, cdata_ptr, perr) != -1:
            return

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        if perr[0] == _lib.xorn_error_invalid_object_data:
            raise ValueError, "invalid object data"
        if perr[0] == _lib.xorn_error_invalid_parent:
            raise ValueError, "can't set attached object " \
                              "to something other than text"
        if perr[0] == _lib.xorn_error_invalid_existing_child:
            raise ValueError, "can't set object with attached objects " \
                              "to something other than net or component"
        if perr[0] == _lib.xorn_error_out_of_memory:
            raise MemoryError
        if perr[0] == _lib.xorn_error_invalid_argument:
            raise SystemError, "error preparing object data"
        raise SystemError, "invalid Xorn error code"

    ## Change the location of an object in the object structure of a
    ## transient revision.
    #
    # This function performs two distinct operations:
    #
    # 1. Change the order in which an object is drawn and written to
    #    files as compared to its sibling objects.
    #
    # 2. Attach a schematic text object to a schematic net or component
    #    object.  As far as this library is concerned, this will cause
    #    the text to be copied and deleted along with the net or component.
    #
    # If \a attach_to is \c None, the object becomes un-attached.  If \a
    # ob and \a insert_before are identical, the revision is left unchanged.
    #
    # \param ob             The object which should be reordered
    #                       and/or attached (must be Text if \a
    #                       attach_to is not \c None)
    # \param attach_to      The object to which \a ob should be attached
    #                       (must be Net or Component, or \c None)
    # \param insert_before  An object already attached to \a attach_to
    #                       before which \a ob should be inserted, or
    #                       \c None to append it at the end.
    #
    # \return \c None
    #
    # \throw ValueError  if the revision isn't transient
    # \throw KeyError    if \a ob or (if not \c None) \a attach_to or
    #                    \a insert_before don't exist in the revision
    # \throw ValueError  if \a attach_to is not \c None and
    #                    - \a ob is not a schematic text or
    #                    - \a attach_to is not a schematic net or
    #                      schematic component
    # \throw ValueError  if \a insert_before is not \c None and not
    #                    attached to \a attach_to
    # \throw MemoryError if there is not enough memory
    #
    # Example:
    # \snippet storage_funcs.py add attribute

    def relocate_object(self, ob, attach_to, insert_before):
        """rev.relocate_object(ob, insert_before) --
           change the location of an object in the object structure
           
           Only callable on a transient revision.
        """

        _check_object_type(Object, ob, 'Revision.relocate_object', 'ob', 1)

        if attach_to is not None and not isinstance(attach_to, Object):
            raise TypeError, \
                "Revision.relocate_object() argument 2 ('attach_to') " \
                "must be %.50s or None, not %.50s" \
                  % (Object.__name__, attach_to.__class__.__name__)

        if insert_before is not None and not isinstance(insert_before, Object):
            raise TypeError, \
                "Revision.relocate_object() argument 3 ('insert_before') " \
                "must be %.50s or None, not %.50s" \
                  % (Object.__name__, insert_before.__class__.__name__)

        perr = _ffi.new('xorn_error_t *')
        if _lib.xorn_relocate_object(
                self._cdata, ob._cdata,
                _ffi.NULL if attach_to is None else attach_to._cdata,
                _ffi.NULL if insert_before is None else insert_before._cdata,
                perr) != -1:
            return

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        if perr[0] == _lib.xorn_error_object_doesnt_exist:
            raise KeyError, "object does not exist"
        if perr[0] == _lib.xorn_error_parent_doesnt_exist:
            raise KeyError, "parent object does not exist"
        if perr[0] == _lib.xorn_error_invalid_parent:
            if _lib.xorn_get_object_type(self._cdata, ob._cdata) \
                   != _lib.xornsch_obtype_text:
                raise ValueError, "only text objects can be attached"
            raise ValueError, "can only attach to net and component objects"
        if perr[0] == _lib.xorn_error_successor_doesnt_exist:
            raise KeyError, "reference object does not exist"
        if perr[0] == _lib.xorn_error_successor_not_sibling:
            raise ValueError, "invalid reference object"
        if perr[0] == _lib.xorn_error_out_of_memory:
            raise MemoryError
        raise SystemError, "invalid Xorn error code"

    ## Copy an object to a transient revision.
    #
    # Any objects attached to \a ob are copied as well, their copies
    # being attached to the copy of \a ob, which is appended to the
    # end of the object list.
    #
    # \param self Destination revision (must be transient)
    # \param rev  Source revision (does not need to be transient)
    # \param ob   %Object in the source revision which should be copied
    #
    # \return Returns the copy of \a ob.
    #
    # \throw ValueError  if \a self isn't transient
    # \throw KeyError    if \a ob doesn't exist in \a rev
    # \throw MemoryError if there is not enough memory

    def copy_object(self, rev, ob):
        """dest.copy_object(src, ob) -> Object --
           copy an object to the revision
           
           Only callable on a transient revision.
        """

        _check_object_type(Revision, rev, 'Revision.copy_object', 'rev', 1)
        _check_object_type(Object, ob, 'Revision.copy_object', 'ob', 2)

        perr = _ffi.new('xorn_error_t *')
        ob_cdata = _lib.xorn_copy_object(
            self._cdata, rev._cdata, ob._cdata, perr)
        if ob_cdata != _ffi.NULL:
            return Object(ob_cdata)

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        if perr[0] == _lib.xorn_error_object_doesnt_exist:
            raise KeyError, "object does not exist in source revision"
        if perr[0] == _lib.xorn_error_out_of_memory:
            raise MemoryError
        raise SystemError, "invalid Xorn error code"

    ## Copy some objects to a transient revision.
    #
    # Any objects attached to the objects are copied as well and
    # attached to the corresponding new object.  The copied objects
    # are appended to the end of the object list in an unspecified
    # order.
    #
    # \param self Destination revision (must be transient)
    # \param rev  Source revision (does not need to be transient)
    # \param sel  Objects in the source revision which should be copied
    #
    # \return Returns a selection containing the copied objects,
    #         excluding attached objects.
    #
    # \throw ValueError  if \a self isn't transient
    # \throw MemoryError if there is not enough memory

    def copy_objects(self, rev, sel):
        """dest.copy_objects(src, sel) -> Selection --
           copy some objects to the revision
           
           Only callable on a transient revision.
        """

        _check_object_type(Revision, rev, 'Revision.copy_objects', 'rev', 1)
        _check_object_type(Selection, sel, 'Revision.copy_objects', 'sel', 2)

        perr = _ffi.new('xorn_error_t *')
        sel_cdata = _lib.xorn_copy_objects(
            self._cdata, rev._cdata, sel._cdata, perr)
        if sel_cdata != _ffi.NULL:
            return Selection(sel_cdata)

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        if perr[0] == _lib.xorn_error_out_of_memory:
            raise MemoryError
        raise SystemError, "invalid Xorn error code"

    ## Delete an object from a transient revision.
    #
    # Any objects attached to \a ob are deleted as well.
    #
    # The deleted object(s) stay valid and can later be re-added using
    # \ref set_object_data.
    #
    # \return \c None
    #
    # \throw ValueError if the revision isn't transient
    # \throw KeyError   if \a ob doesn't exist in the revision

    def delete_object(self, ob):
        """rev.delete_object(ob) -- delete an object from the revision
           
           Only callable on a transient revision.
        """

        _check_object_type(Object, ob, 'Revision.delete_object', 'ob', 1)

        perr = _ffi.new('xorn_error_t *')
        if _lib.xorn_delete_object(self._cdata, ob._cdata, perr) != -1:
            return

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        if perr[0] == _lib.xorn_error_object_doesnt_exist:
            raise KeyError, "object does not exist"
        raise SystemError, "invalid Xorn error code"

    ## Delete some objects from a transient revision.
    #
    # Any objects attached to a deleted object are deleted as well.
    #
    # The deleted objects stay valid and can later be re-added using
    # \ref set_object_data.
    #
    # Objects that don't exist in the revision are ignored.
    #
    # \return \c None
    #
    # \throw ValueError if the revision isn't transient

    def delete_objects(self, sel):
        """rev.delete_objects(sel) -- delete some objects from the revision
           
           Only callable on a transient revision.
        """

        _check_object_type(Selection, sel, 'Revision.delete_objects', 'sel', 1)

        perr = _ffi.new('xorn_error_t *')

        if _lib.xorn_delete_selected_objects(
                self._cdata, sel._cdata, perr) != -1:
            return

        if perr[0] == _lib.xorn_error_revision_not_transient:
            raise ValueError, "revision can only be changed while transient"
        raise SystemError, "invalid Xorn error code"


## The identity of an object across revisions.
#
# A value of this type is used as a key to look up and change the
# state of an object in a revision.  It is created by
# Revision.add_object, Revision.copy_object, or (indirectly)
# Revision.copy_objects or returned by one of the other functions of
# this module.
#
# This type can't be directly instantiated.

class Object(object):
    """The identity of an object across revisions."""

    def __init__(self, _cdata):
        _check_object_type(_ffi.CData, _cdata,
                           'Object.__init__', '_cdata', 1)
        if _cdata == _ffi.NULL:
            raise MemoryError
        self._cdata = _cdata

    ## x.__cmp__(y) <==> cmp(x,y)
    def __cmp__(self, other):
        if not isinstance(other, Object):
            return NotImplemented
        return cmp(self._cdata, other._cdata)

    ## x.__hash__() <==> hash(x)
    def __hash__(self):
        return hash((Object, self._cdata))


## The identity of a set of objects across revisions.
#
# A value of this type is used as a set of keys for mass object
# inspection or manipulation and does not designate a specific order
# of the objects.  It is created using one of the \c
# select_<em>something</em> class of functions.
#
# This type can't be directly instantiated.

class Selection(object):
    """The identity of a set of objects across revisions."""

    def __init__(self, _cdata):
        _check_object_type(_ffi.CData, _cdata,
                           'Selection.__init__', '_cdata', 1)
        if _cdata == _ffi.NULL:
            raise MemoryError
        self._cdata = _cdata


## Return a list of objects in a revision which are attached to a
## certain object.
#
# If \a ob is \c None, return all objects in the revision which are
# *not* attached.  The objects are returned in their actual order.
# Objects attached to the returned objects are not returned.
#
# \throw KeyError    if \a ob is not \c None and does not exist in \a rev
# \throw MemoryError if there is not enough memory

def get_objects_attached_to(rev, ob):
    # returns [Object]
    """a list of objects in a revision which are attached to a certain object"""

    _check_object_type(Revision, rev, 'get_objects_attached_to', 'rev', 1)

    if ob is None:
        ob_cdata = _ffi.NULL
    else:
        if not isinstance(ob, Object):
            raise TypeError, \
                "get_objects_attached_to() argument 2 must be %.50s or " \
                "None, not %.50s" % (Object.__name__, ob.__class__.__name__)
        if not _lib.xorn_object_exists_in_revision(rev._cdata, ob._cdata):
            raise KeyError, "object does not exist"
        ob_cdata = ob._cdata

    pobjects = _ffi.new('xorn_object_t **')
    pcount = _ffi.new('size_t *')

    if _lib.xorn_get_objects_attached_to(rev._cdata, ob_cdata,
                                         pobjects, pcount) == -1:
        raise MemoryError

    # objects is a <cdata 'struct xorn_object * *'>: an array of
    # xorn_object_t values
    # count is an integer

    l = [Object(pobjects[0][i]) for i in xrange(pcount[0])]
    _lib.free(pobjects[0])
    return l

## Return a list of objects which are in a revision as well as in a
## selection.
#
# The objects are not necessarily returned in a meaningful order.
#
# \throw MemoryError if there is not enough memory

def get_selected_objects(rev, sel):
    # returns [Object]
    """a list of objects which are in a revision as well as in a selection"""

    _check_object_type(Revision, rev, 'get_selected_objects', 'rev', 1)
    _check_object_type(Selection, sel, 'get_selected_objects', 'sel', 2)

    pobjects = _ffi.new('xorn_object_t **')
    pcount = _ffi.new('size_t *')

    if _lib.xorn_get_selected_objects(rev._cdata, sel._cdata,
                                      pobjects, pcount) == -1:
        return MemoryError

    l = [Object(pobjects[0][i]) for i in xrange(pcount[0])]
    _lib.free(pobjects[0])
    return l

## Return a list of objects which are in one revision but not in
## another.
#
# Returns objects in \a to_rev which are not in \a from_rev.  They are
# not necessarily returned in a meaningful order.
#
# \throw MemoryError if there is not enough memory

def get_added_objects(from_rev, to_rev):
    # returns [Object]
    """a list of objects which are in one revision but not in another"""

    _check_object_type(Revision, from_rev, 'get_added_objects', 'from_rev', 1)
    _check_object_type(Revision, to_rev, 'get_added_objects', 'to_rev', 2)

    pobjects = _ffi.new('xorn_object_t **')
    pcount = _ffi.new('size_t *')

    if _lib.xorn_get_added_objects(from_rev._cdata, to_rev._cdata,
                                   pobjects, pcount) == -1:
        return MemoryError

    l = [Object(pobjects[0][i]) for i in xrange(pcount[0])]
    _lib.free(pobjects[0])
    return l

## Return a list of objects which are in one revision but not in
## another.
#
# Returns objects in \a from_rev which are not in \a to_rev.  They are
# not necessarily returned in a meaningful order.
#
# \throw MemoryError if there is not enough memory

def get_removed_objects(from_rev, to_rev):
    # returns [Object]
    """a list of objects which are in one revision but not in another"""

    _check_object_type(Revision, from_rev, 'get_removed_objects', 'from_rev', 1)
    _check_object_type(Revision, to_rev, 'get_removed_objects', 'to_rev', 2)

    pobjects = _ffi.new('xorn_object_t **')
    pcount = _ffi.new('size_t *')

    if _lib.xorn_get_removed_objects(from_rev._cdata, to_rev._cdata,
                                     pobjects, pcount) == -1:
        return MemoryError

    l = [Object(pobjects[0][i]) for i in xrange(pcount[0])]
    _lib.free(pobjects[0])
    return l

## Return a list of objects which exist in two revisions but have
## different type or data.
#
# The objects are not necessarily returned in a meaningful order.
#
# \throw MemoryError if there is not enough memory

def get_modified_objects(from_rev, to_rev):
    # returns [Object]
    """a list of objects which exist in two revisions but have different
       type or data"""

    _check_object_type(Revision, from_rev,
                       'get_modified_objects', 'from_rev', 1)
    _check_object_type(Revision, to_rev,
                       'get_modified_objects', 'to_rev', 2)

    pobjects = _ffi.new('xorn_object_t **')
    pcount = _ffi.new('size_t *')

    if _lib.xorn_get_modified_objects(from_rev._cdata, to_rev._cdata,
                                      pobjects, pcount) == -1:
        raise MemoryError

    l = [Object(pobjects[0][i]) for i in xrange(pcount[0])]
    _lib.free(pobjects[0])
    return l

## Return an empty selection.
#
# \throw MemoryError if there is not enough memory

def select_none():
    # returns Selection
    """an empty selection"""

    return Selection(_lib.xorn_select_none())

## Return a selection containing a single object.
#
# \throw MemoryError if there is not enough memory

def select_object(ob):
    # returns Selection
    """a selection containing a single object"""

    _check_object_type(Object, ob, 'select_object', 'ob', 1)
    return Selection(_lib.xorn_select_object(ob._cdata))

## Return a selection containing all objects in a revision attached to
## a given object.
#
# The object may be \c None, in which case the selection contains all
# objects which are *not* attached.
#
# \throw KeyError    if \a ob is not \c None and does not exist in \a rev
# \throw MemoryError if there is not enough memory

def select_attached_to(rev, ob):
    # returns Selection
    """a selection containing all objects in a revision attached to a
       given object"""

    _check_object_type(Revision, rev, 'select_attached_to', 'rev', 1)
    if ob is None:
        return Selection(_lib.xorn_select_attached_to(rev._cdata, _ffi.NULL))

    if not isinstance(ob, Object):
        raise TypeError, \
            "select_attached_to() argument 2 ('ob') must be %.50s or None, " \
            "not %.50s" % (Object.__name__, ob.__class__.__name__)
    if _lib.xorn_object_exists_in_revision(rev._cdata, ob._cdata) == 0:
        raise KeyError, "object does not exist"
    return Selection(_lib.xorn_select_attached_to(rev._cdata, ob._cdata))

## Return a selection containing all objects in a revision.
#
# \throw MemoryError if there is not enough memory

def select_all(rev):
    # returns Selection
    """a selection containing all objects in a revision"""

    _check_object_type(Revision, rev, 'select_all', 'rev', 1)
    return Selection(_lib.xorn_select_all(rev._cdata))

## Return a selection containing all objects in a revision except
## those in a given selection.
#
# \throw MemoryError if there is not enough memory

def select_all_except(rev, sel):
    # returns Selection
    """a selection containing all objects in a revision except those in a
       given selection"""

    _check_object_type(Revision, rev, 'select_all_except', 'rev', 1)
    _check_object_type(Selection, sel, 'select_all_except', 'sel', 2)
    return Selection(_lib.xorn_select_all_except(rev._cdata, sel._cdata))

## Return a selection which contains all the objects in an existing
## selection plus a given object.
#
# \throw MemoryError if there is not enough memory

def select_including(sel, ob):
    # returns Selection
    """a selection which contains all the objects in an existing selection
       plus a given object"""

    _check_object_type(Selection, sel, 'select_including', 'sel', 1)
    _check_object_type(Object, ob, 'select_including', 'ob', 2)
    return Selection(_lib.xorn_select_including(sel._cdata, ob._cdata))

## Return a selection which contains all the objects in an existing
## selection minus a given object.
#
# \throw MemoryError if there is not enough memory

def select_excluding(sel, ob):
    # returns Selection
    """a selection which contains all the objects in an existing selection
       minus a given object"""

    _check_object_type(Selection, sel, 'select_excluding', 'sel', 1)
    _check_object_type(Object, ob, 'select_excluding', 'ob', 2)
    return Selection(_lib.xorn_select_excluding(sel._cdata, ob._cdata))

## Return a selection containing the objects in either given
## selection.
#
# \throw MemoryError if there is not enough memory

def select_union(sel0, sel1):
    # returns Selection
    """a selection containing the objects in either given selection"""

    _check_object_type(Selection, sel0, 'select_union', 'sel0', 1)
    _check_object_type(Selection, sel1, 'select_union', 'sel1', 2)
    return Selection(_lib.xorn_select_union(sel0._cdata, sel1._cdata))

## Return a selection containing the objects in both given selections.
#
# \throw MemoryError if there is not enough memory

def select_intersection(sel0, sel1):
    # returns Selection
    """a selection containing the objects in both given selections"""

    _check_object_type(Selection, sel0, 'select_intersection', 'sel0', 1)
    _check_object_type(Selection, sel1, 'select_intersection', 'sel1', 2)
    return Selection(_lib.xorn_select_intersection(sel0._cdata, sel1._cdata))

## Return a selection containing the objects contained in one given
## selection, but not the other.
#
# \throw MemoryError if there is not enough memory

def select_difference(sel0, sel1):
    # returns Selection
    """a selection containing the objects contained in one given
       selection, but not the other"""

    _check_object_type(Selection, sel0, 'select_difference', 'sel0', 1)
    _check_object_type(Selection, sel1, 'select_difference', 'sel1', 2)
    return Selection(_lib.xorn_select_difference(sel0._cdata, sel1._cdata))

## Return whether a selection is empty in a given revision.

def selection_is_empty(rev, sel):
    # returns bool
    """whether a selection is empty in a given revision"""

    _check_object_type(Revision, rev, 'selection_is_empty', 'rev', 1)
    _check_object_type(Selection, sel, 'selection_is_empty', 'sel', 2)
    return _TO_BOOL[_lib.xorn_selection_is_empty(rev._cdata, sel._cdata)]

## Return whether an object exists in a revision and is selected in a
## selection.

def object_is_selected(rev, sel, ob):
    # returns bool
    """whether an object exists in a revision and is selected in a selection"""

    _check_object_type(Revision, rev, 'object_is_selected', 'rev', 1)
    _check_object_type(Selection, sel, 'object_is_selected', 'sel', 2)
    _check_object_type(Object, ob, 'object_is_selected', 'ob', 3)
    return _TO_BOOL[_lib.xorn_object_is_selected(rev._cdata, sel._cdata,
                                                 ob._cdata)]

class _Data(object):
    ## x.__cmp__(y) <==> cmp(x,y)
    def __cmp__(self, other):
        size = _ffi.sizeof(self._cdata)
        if _ffi.sizeof(other._cdata) != size or \
           _ffi.typeof(other._cdata) != _ffi.typeof(self._cdata):
            return NotImplemented
        return _lib.memcmp(_ffi.addressof(self._cdata),
                           _ffi.addressof(other._cdata), size)

## Schematic line style.

class LineAttr(_Data):
    width = _RenameDescriptor('width')
    cap_style = _RenameDescriptor('cap_style')
    dash_style = _RenameDescriptor('dash_style')
    dash_length = _RenameDescriptor('dash_length')
    dash_space = _RenameDescriptor('dash_space')

    def __init__(self, width = 0., cap_style = 0, dash_style = 0,
                       dash_length = 0., dash_space = 0.,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'LineAttr', '_cdata', 6)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._cdata = _cdata
            return

        _check_object_type(float, width, 'LineAttr', 'width', 1)
        _check_object_type(int, cap_style, 'LineAttr', 'cap_style', 2)
        _check_object_type(int, dash_style, 'LineAttr', 'dash_style', 3)
        _check_object_type(float, dash_length, 'LineAttr', 'dash_length', 4)
        _check_object_type(float, dash_space, 'LineAttr', 'dash_space', 5)

        self._cdata = _ffi.new('struct xornsch_line_attr *')[0]
        self.width = width
        self.cap_style = cap_style
        self.dash_style = dash_style
        self.dash_length = dash_length
        self.dash_space = dash_space

## Schematic fill style.

class FillAttr(_Data):
    type = _RenameDescriptor('type')
    width = _RenameDescriptor('width')
    angle0 = _RenameDescriptor('angle0')
    pitch0 = _RenameDescriptor('pitch0')
    angle1 = _RenameDescriptor('angle1')
    pitch1 = _RenameDescriptor('pitch1')

    def __init__(self, type = 0, width = 0., angle0 = 0, pitch0 = 0.,
                                             angle1 = 0, pitch1 = 0.,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'FillAttr', '_cdata', 7)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._cdata = _cdata
            return

        _check_object_type(int, type, 'FillAttr', 'type', 1)
        _check_object_type(float, width, 'FillAttr', 'width', 2)
        _check_object_type(int, angle0, 'FillAttr', 'angle0', 3)
        _check_object_type(float, pitch0, 'FillAttr', 'pitch0', 4)
        _check_object_type(int, angle1, 'FillAttr', 'angle1', 5)
        _check_object_type(float, pitch1, 'FillAttr', 'pitch1', 6)

        self._cdata = _ffi.new('struct xornsch_fill_attr *')[0]
        self.type = type
        self.width = width
        self.angle0 = angle0
        self.pitch0 = pitch0
        self.angle1 = angle1
        self.pitch1 = pitch1

## Schematic arc.

class Arc(_Data):
    """Schematic arc."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    radius = _RenameDescriptor('radius')
    startangle = _RenameDescriptor('startangle')
    sweepangle = _RenameDescriptor('sweepangle')
    color = _RenameDescriptor('color')
    line = _LineDescriptor()

    def __init__(self, x = 0., y = 0., radius = 0.,
                       startangle = 0, sweepangle = 0, color = 0, line = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Arc', '_cdata', 8)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_arc
            self._cdata = _cdata
            self._line = None
            return

        _check_object_type(float, x, 'Arc', 'x', 1)
        _check_object_type(float, y, 'Arc', 'y', 2)
        _check_object_type(float, radius, 'Arc', 'radius', 3)
        _check_object_type(int, startangle, 'Arc', 'startangle', 4)
        _check_object_type(int, sweepangle, 'Arc', 'sweepangle', 5)
        _check_object_type(int, color, 'Arc', 'color', 6)

        if line is not None and not isinstance(line, LineAttr):
            raise TypeError, "line attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, line.__class__.__name__)

        self._obtype = _lib.xornsch_obtype_arc
        self._cdata = _ffi.new('struct xornsch_arc *')[0]
        self._line = None
        self.x = x
        self.y = y
        self.radius = radius
        self.startangle = startangle
        self.sweepangle = sweepangle
        self.color = color
        if line is not None:
            self.line = line

## Schematic box.

class Box(_Data):
    """Schematic box."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    width = _RenameDescriptor('size', 'x')
    height = _RenameDescriptor('size', 'y')
    color = _RenameDescriptor('color')
    line = _LineDescriptor()
    fill = _FillDescriptor()

    def __init__(self, x = 0., y = 0., width = 0., height = 0.,
                       color = 0, line = None, fill = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Box', '_cdata', 8)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_box
            self._cdata = _cdata
            self._line = None
            self._fill = None
            return

        _check_object_type(float, x, 'Box', 'x', 1)
        _check_object_type(float, y, 'Box', 'y', 2)
        _check_object_type(float, width, 'Box', 'width', 3)
        _check_object_type(float, height, 'Box', 'height', 4)
        _check_object_type(int, color, 'Box', 'color', 5)

        if line is not None and not isinstance(line, LineAttr):
            raise TypeError, "line attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, line.__class__.__name__)

        if fill is not None and not isinstance(fill, FillAttr):
            raise TypeError, "fill attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, fill.__class__.__name__)

        self._obtype = _lib.xornsch_obtype_box
        self._cdata = _ffi.new('struct xornsch_box *')[0]
        self._line = None
        self._fill = None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        if line is not None:
            self.line = line
        if fill is not None:
            self.fill = fill


## Schematic circle.

class Circle(_Data):
    """Schematic circle."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    radius = _RenameDescriptor('radius')
    color = _RenameDescriptor('color')
    line = _LineDescriptor()
    fill = _FillDescriptor()

    def __init__(self, x = 0., y = 0., radius = 0.,
                       color = 0, line = None, fill = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Circle', '_cdata', 7)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_circle
            self._cdata = _cdata
            self._line = None
            self._fill = None
            return

        _check_object_type(float, x, 'Circle', 'x', 1)
        _check_object_type(float, y, 'Circle', 'y', 2)
        _check_object_type(float, radius, 'Circle', 'radius', 3)
        _check_object_type(int, color, 'Circle', 'color', 4)

        if line is not None and not isinstance(line, LineAttr):
            raise TypeError, "line attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, line.__class__.__name__)

        if fill is not None and not isinstance(fill, FillAttr):
            raise TypeError, "fill attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, fill.__class__.__name__)

        self._obtype = _lib.xornsch_obtype_circle
        self._cdata = _ffi.new('struct xornsch_circle *')[0]
        self._line = None
        self._fill = None
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        if line is not None:
            self.line = line
        if fill is not None:
            self.fill = fill


## Schematic component.

class Component(_Data):
    """Schematic component."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    selectable = _RenameDescriptor('selectable')
    angle = _RenameDescriptor('angle')
    mirror = _RenameDescriptor('mirror')
    symbol = _PointerDescriptor('symbol')

    def __init__(self, x = 0., y = 0., selectable = False,
                       angle = 0, mirror = False, symbol = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Component', '_cdata', 7)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_component
            self._cdata = _cdata
            if _cdata.symbol.ptr == _ffi.NULL:
                self._p_symbol = None
            else:
                self._p_symbol = _ffi.from_handle(_cdata.symbol.ptr)
            return

        _check_object_type(float, x, 'Component', 'x', 1)
        _check_object_type(float, y, 'Component', 'y', 2)
        _check_object_type(bool, selectable, 'Component', 'selectable', 3)
        _check_object_type(int, angle, 'Component', 'angle', 4)
        _check_object_type(bool, mirror, 'Component', 'mirror', 5)
        # symbol can be any type

        self._obtype = _lib.xornsch_obtype_component
        self._cdata = _ffi.new('struct xornsch_component *')[0]
        self._p_symbol = None
        self.x = x
        self.y = y
        self.selectable = selectable
        self.angle = angle
        self.mirror = mirror
        self.symbol = symbol

## Schematic line.

class Line(_Data):
    """Schematic line."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    width = _RenameDescriptor('size', 'x')
    height = _RenameDescriptor('size', 'y')
    color = _RenameDescriptor('color')
    line = _LineDescriptor()

    def __init__(self, x = 0., y = 0., width = 0., height = 0.,
                       color = 0, line = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Line', '_cdata', 7)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_line
            self._cdata = _cdata
            self._line = None
            return

        _check_object_type(float, x, 'Line', 'x', 1)
        _check_object_type(float, y, 'Line', 'y', 2)
        _check_object_type(float, width, 'Line', 'width', 3)
        _check_object_type(float, height, 'Line', 'height', 4)
        _check_object_type(int, color, 'Line', 'color', 5)

        if line is not None and not isinstance(line, LineAttr):
            raise TypeError, "line attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, line.__class__.__name__)

        self._obtype = _lib.xornsch_obtype_line
        self._cdata = _ffi.new('struct xornsch_line *')[0]
        self._line = None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        if line is not None:
            self.line = line

## Schematic net segment, bus segment, or pin.

class Net(_Data):
    """Schematic net segment, bus segment, or pin."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    width = _RenameDescriptor('size', 'x')
    height = _RenameDescriptor('size', 'y')
    color = _RenameDescriptor('color')
    is_bus = _RenameDescriptor('is_bus')
    is_pin = _RenameDescriptor('is_pin')
    is_inverted = _RenameDescriptor('is_inverted')

    def __init__(self, x = 0., y = 0., width = 0., height = 0., color = 0,
                       is_bus = False, is_pin = False, is_inverted = False,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Net', '_cdata', 9)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_net
            self._cdata = _cdata
            return

        _check_object_type(float, x, 'Net', 'x', 1)
        _check_object_type(float, y, 'Net', 'y', 2)
        _check_object_type(float, width, 'Net', 'width', 3)
        _check_object_type(float, height, 'Net', 'height', 4)
        _check_object_type(int, color, 'Net', 'color', 5)
        _check_object_type(bool, is_bus, 'Net', 'is_bus', 6)
        _check_object_type(bool, is_pin, 'Net', 'is_pin', 7)
        _check_object_type(bool, is_inverted, 'Net', 'is_inverted', 8)

        self._obtype = _lib.xornsch_obtype_net
        self._cdata = _ffi.new('struct xornsch_net *')[0]
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.is_bus = is_bus
        self.is_pin = is_pin
        self.is_inverted = is_inverted

## Schematic path.

class Path(_Data):
    """Schematic path."""

    pathdata = _StringDescriptor('pathdata')
    color = _RenameDescriptor('color')
    line = _LineDescriptor()
    fill = _FillDescriptor()

    def __init__(self, pathdata = '', color = 0, line = None, fill = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Path', '_cdata', 5)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_path
            self._cdata = _cdata
            self._line = None
            self._fill = None
            return

        _check_object_type(str, pathdata, 'Path', 'pathdata', 1)
        _check_object_type(int, color, 'Path', 'color', 2)

        if line is not None and not isinstance(line, LineAttr):
            raise TypeError, "line attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, line.__class__.__name__)

        if fill is not None and not isinstance(fill, FillAttr):
            raise TypeError, "fill attribute must be %.50s or None, " \
                "not %.50s" % (_ffi.CData.__name__, fill.__class__.__name__)

        self._obtype = _lib.xornsch_obtype_path
        self._cdata = _ffi.new('struct xornsch_path *')[0]
        self._line = None
        self._fill = None
        self.pathdata = pathdata
        self.color = color
        if line is not None:
            self.line = line
        if fill is not None:
            self.fill = fill

## Schematic picture.

class Picture(_Data):
    """Schematic picture."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    width = _RenameDescriptor('size', 'x')
    height = _RenameDescriptor('size', 'y')
    angle = _RenameDescriptor('angle')
    mirror = _RenameDescriptor('mirror')
    pixmap = _PointerDescriptor('pixmap')

    def __init__(self, x = 0., y = 0., width = 0., height = 0.,
                       angle = 0, mirror = False, pixmap = None,
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Picture', '_cdata', 8)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_picture
            self._cdata = _cdata
            if _cdata.pixmap.ptr == _ffi.NULL:
                self._p_pixmap = None
            else:
                self._p_pixmap = _ffi.from_handle(_cdata.pixmap.ptr)
            return

        _check_object_type(float, x, 'Picture', 'x', 1)
        _check_object_type(float, y, 'Picture', 'y', 2)
        _check_object_type(float, width, 'Picture', 'width', 3)
        _check_object_type(float, height, 'Picture', 'height', 4)
        _check_object_type(int, angle, 'Picture', 'angle', 5)
        _check_object_type(bool, mirror, 'Picture', 'mirror', 6)
        # pixmap can be any type

        self._obtype = _lib.xornsch_obtype_picture
        self._cdata = _ffi.new('struct xornsch_picture *')[0]
        self._p_pixmap = None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle
        self.mirror = mirror
        self.pixmap = pixmap

## Schematic text or attribute.

class Text(_Data):
    """Schematic text or attribute."""

    x = _RenameDescriptor('pos', 'x')
    y = _RenameDescriptor('pos', 'y')
    color = _RenameDescriptor('color')
    text_size = _RenameDescriptor('text_size')
    visibility = _RenameDescriptor('visibility')
    show_name_value = _RenameDescriptor('show_name_value')
    angle = _RenameDescriptor('angle')
    alignment = _RenameDescriptor('alignment')
    text = _StringDescriptor('text')

    def __init__(self, x = 0., y = 0., color = 0, text_size = 0,
                       visibility = False, show_name_value = 0,
                       angle = 0, alignment = 0, text = '',
                 _cdata = None):
        if _cdata is not None:
            _check_object_type(_ffi.CData, _cdata, 'Text', '_cdata', 10)
            if _cdata == _ffi.NULL:
                raise MemoryError
            self._obtype = _lib.xornsch_obtype_text
            self._cdata = _cdata
            return

        _check_object_type(float, x, 'Text', 'x', 1)
        _check_object_type(float, y, 'Text', 'y', 2)
        _check_object_type(int, color, 'Text', 'color', 3)
        _check_object_type(int, text_size, 'Text', 'text_size', 4)
        _check_object_type(bool, visibility, 'Text', 'visibility', 5)
        _check_object_type(int, show_name_value, 'Text', 'show_name_value', 6)
        _check_object_type(int, angle, 'Text', 'angle', 7)
        _check_object_type(int, alignment, 'Text', 'alignment', 8)
        _check_object_type(str, text, 'Text', 'text', 9)

        self._obtype = _lib.xornsch_obtype_text
        self._cdata = _ffi.new('struct xornsch_text *')[0]
        self.x = x
        self.y = y
        self.color = color
        self.text_size = text_size
        self.visibility = visibility
        self.show_name_value = show_name_value
        self.angle = angle
        self.alignment = alignment
        self.text = text
