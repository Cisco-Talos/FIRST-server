#-------------------------------------------------------------------------------
#
#   FIRST Engine: Mnemonic Hash
#   Uses Distorm3 to obtain mnemonics from the opcodes, reduces the opcodes to
#   a single string and hashes it for future lookup
#
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
#   Requirements
#   ------------
#   -   distorm3
#   -   mongoengine
#
#-------------------------------------------------------------------------------

#   Python Modules
from hashlib import sha256

#   FIRST Modules
from first.error import FIRSTError
from first.engines import AbstractEngine
from first.engines.results import FunctionResult

#   Third Party Modules
from bson.objectid import ObjectId
from distorm3 import DecomposeGenerator, Decode32Bits, Decode64Bits, Decode16Bits
from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine import Document, StringField, ListField, ObjectIdField

class MnemonicHash(Document):
    sha256 = StringField(max_length=64, required=True)
    architecture = StringField(max_length=64, required=True)
    functions = ListField(ObjectIdField(), default=list)

    meta = {
        'indexes' : [('sha256', 'architecture')]
    }

    def dump(self):
        return {'sha256' : self.sha256,
                'architecture' : self.architecture,
                'functions' : self.function_list()}

    def function_list(self):
        return [str(x) for x in self.functions]


class MnemonicHashEngine(AbstractEngine):
    _name = 'MnemonicHash'
    _description = ('Uses mnemonics from the opcodes to generate a hash '
                    '(Intel Only). Requires at least 8 mnemonics.')
    _required_db_names = ['first_db']

    def mnemonic_hash(self, opcodes, architecture):
        dt = None
        mapping = {'intel32' : Decode32Bits,
                    'intel64' : Decode64Bits,
                    'intel16' : Decode16Bits}
        if architecture in mapping:
            dt = mapping[architecture]
        else:
            return (None, None)

        try:
            iterable = DecomposeGenerator(0, opcodes, dt)

            #   Uses valid to ensure we are not creating hashes with 'db 0xYY'
            mnemonics = [d.mnemonic for d in iterable if d.valid]
            return (mnemonics, sha256(''.join(mnemonics)).hexdigest())

        except Exception as e:
            return (None, None)

    def _add(self, function):
        '''
        Nothing needs to be implemented since the Function Model has the
        sha256 of the opcodes
        '''
        opcodes = function['opcodes']
        architecture = function['architecture']
        mnemonics, mnemonic_sha256 = self.mnemonic_hash(opcodes, architecture)

        if (not mnemonic_sha256) or (not mnemonics) or (8 > len(mnemonics)):
            return

        try:
            db_obj = MnemonicHash.objects(  sha256=mnemonic_sha256,
                                            architecture=architecture).get()
        except DoesNotExist:
            db_obj = MnemonicHash(  sha256=mnemonic_sha256,
                                    architecture=architecture)

        function_id = ObjectId(function['id'])
        if function_id not in db_obj.functions:
            db_obj.functions.append(function_id)
            db_obj.save()

    def _scan(self, opcodes, architecture, apis):
        '''Returns List of tuples (function ID, similarity percentage)'''
        db = self._dbs['first_db']
        mnemonics, mnemonic_sha256 = self.mnemonic_hash(opcodes, architecture)

        if (not mnemonic_sha256) or (not mnemonics) or (8 > len(mnemonics)):
            return

        try:
            db_obj = MnemonicHash.objects(  sha256=mnemonic_sha256,
                                            architecture=architecture).get()
        except DoesNotExist:
            return None

        results = []
        for function_id in db_obj.function_list():
            similarity = 75.0
            function = db.find_function(_id=ObjectId(function_id))

            if not function or not function.metadata:
                continue

            #   The APIs will count up to 10% of the similarity score
            total_apis = len(function.apis)
            overlap = float(len(set(function.apis).intersection(apis)))
            if 0 != total_apis:
                similarity += (overlap / total_apis) * 10

            results.append(FunctionResult(function_id, similarity))

        return results

    def _uninstall(self):
        MnemonicHash.drop_collection()
