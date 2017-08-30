#-------------------------------------------------------------------------------
#
#   FIRST Engine: Exact Match
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
from hashlib import sha256

#   FIRST Modules
from first_core.error import FIRSTError
from first_core.engines import AbstractEngine
from first_core.engines.results import FunctionResult

class ExactMatchEngine(AbstractEngine):
    _name = 'ExactMatch'
    _description = 'Hashes the function\'s opcodes and finds direct matches'
    _required_db_names = ['first_db']

    def _add(self, function):
        '''
        Nothing needs to be implemented since the Function Model has the
        sha256 of the opcodes
        '''
        pass

    def _scan(self, opcodes, architecture, apis):
        '''Returns List of FunctionResults'''

        db = self._dbs['first_db']
        function = db.find_function(h_sha256=sha256(opcodes).hexdigest(),
                                    architecture=architecture)

        if not function:
            return None

        similarity = 90.0
        if set(function.apis.values()) == set(apis):
            similarity += 10.0

        return [FunctionResult(str(function.id), similarity)]
