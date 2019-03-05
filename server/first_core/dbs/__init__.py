#-------------------------------------------------------------------------------
#
#   FIRST's DB Abstract class definition
#   Copyright (C) 2016  Angel M. Villegas
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#-------------------------------------------------------------------------------

#   Python Modules
import configparser 
from hashlib import md5

#   FIRST Modules
from first_core.error import FIRSTError

#   Class for FirstDB related exceptions
class FIRSTDBError(FIRSTError):
    type_name = 'DBError'

class AbstractDB(object):
    _name = 'AbstractDB'
    _is_installed = False
    #
    #   Functions called by FIRST Framework (No Implementation Required)
    #--------------------------------------------------------------------------
    @property
    def name(self):
        '''
        Returns a unqiue String value for this class that doesn't match other
        AbstractDB inheried classes. The string value is a human readable/usable

        @returns String
        '''
        return self._name

    @property
    def is_installed(self):
        return self._is_installed


    #   Functions called by FIRST Framework (Implement Required)
    #--------------------------------------------------------------------------

    def __init__(self, conf):
        '''
        Constructor.

        @param conf: configparser.RawConfigParser
        '''
        raise FIRSTDBError('TODO: implement')




class FIRSTDBManager(object):
    _dbs = {}

    #   TODO: decide whether config is needed
    def __init__(self, config=None):

        for db in possible_dbs:
            try:
                d = db(config)

                if d.is_installed:
                    self._dbs[d.name] = d

            except FIRSTDBError as e:
                print(e)

        if not self._dbs:
            print('[DBM] Error: No dbs could be loaded')

    def db_list(self):
        '''
        Returns
        {
            <db_name> : <db_instance>,
            ...
        }
        '''
        return self._dbs

    @property
    def first_db(self):
        if 'first_db' in self._dbs:
            return self._dbs['first_db']

        return None

    def get(self, db_name):
        if db_name in self._dbs:
            return self._dbs[db_name]

        return None



#   FIRST DB Classes
from first_core.dbs.builtin_db import FIRSTDB

possible_dbs = [FIRSTDB]
