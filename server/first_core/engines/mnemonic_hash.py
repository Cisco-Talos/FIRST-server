#-------------------------------------------------------------------------------
#
#   FIRST Engine: Mnemonic Hash
#   Uses Distorm3 to obtain mnemonics from the opcodes, reduces the opcodes to
#   a single string and hashes it for future lookup
#
#   Copyright (C) 2017  Angel M. Villegas
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
#
#-------------------------------------------------------------------------------

#   Python Modules
from hashlib import sha256

#   FIRST Modules
from first_core.error import FIRSTError
from first_core.engines import AbstractEngine
from first_core.engines.results import FunctionResult

#   Third Party Modules
from capstone import *
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

MIN_REQUIRED_MNEMONICS = 8

class MnemonicHash(models.Model):
    sha256 = models.CharField(max_length=64)
    architecture = models.CharField(max_length=64)
    functions = models.ManyToManyField('MnemonicHashFunctions')

    class Meta:
        app_label = 'engines'
        index_together = ('sha256', 'architecture')
        unique_together = ('sha256', 'architecture')

    def dump(self):
        return {'sha256' : self.sha256,
                'architecture' : self.architecture,
                'functions' : self.functions.all()}

class MnemonicHashFunctions(models.Model):
    func = models.BigIntegerField()

    class Meta:
        app_label = 'engines'


class MnemonicHashEngine(AbstractEngine):
    _name = 'MnemonicHash'
    _description = ('Uses mnemonics from the opcodes to generate a hash '
                    '(architecture support limited to: intel32, intel64, '
                    'arm, arm64, mips32, mips64, ppc32, ppc64, sparc). '
                    'Requires at least 8 mnemonics.')
    _required_db_names = ['first_db']

    def mnemonic_hash(self, disassembly):
        if not disassembly:
            return (None, None)

        try:
            mnemonics = [i.mnemonic for i in disassembly.instructions()]
            if len(mnemonics) < MIN_REQUIRED_MNEMONICS:
                return (None, None)

            return (mnemonics, sha256(''.join(mnemonics)).hexdigest())

        except Exception as e:
            raise e
            return (None, None)

    def _add(self, function):
        '''
        Creates a mnemonic hash based on the provided architecture and opcodes
        via disassembling the opcodes and discarding the instruction operands.
        '''
        architecture = function['architecture']
        disassembly = function.get('disassembly')
        mnemonics, mnemonic_sha256 = self.mnemonic_hash(disassembly)
        if None in [mnemonic_sha256, mnemonics]:
            return

        db_obj, _ = MnemonicHash.objects.get_or_create(sha256=mnemonic_sha256,
                                                    architecture=architecture)
        function_id = function['id']
        count = MnemonicHash.objects.filter(sha256=mnemonic_sha256,
                                            architecture=architecture,
                                            functions__func=function_id).count()

        if not count:
            func, _ = MnemonicHashFunctions.objects.get_or_create(func=function_id)
            db_obj.functions.add(func)

    def _scan(self, opcodes, architecture, apis, disassembly):
        '''Returns List of tuples (function ID, similarity percentage)'''
        db = self._dbs['first_db']
        mnemonics, mnemonic_sha256 = self.mnemonic_hash(disassembly)

        if None in [mnemonic_sha256, mnemonics]:
            return

        try:
            db_obj = MnemonicHash.objects.get(sha256=mnemonic_sha256,
                                                architecture=architecture)
        except ObjectDoesNotExist:
            return None

        results = []
        for f in db_obj.functions.all():
            similarity = 75.0
            function_id = f.func
            function = db.find_function(_id=function_id)

            if (not function) or (not function.metadata.count()):
                continue

            #   The APIs will count up to 10% of the similarity score
            total_apis = function.apis.count()
            if total_apis:
                func_apis = {x['api'] for x in function.apis.values('api')}
                overlap = float(len(func_apis.intersection(apis)))
                similarity += (overlap / total_apis) * 10

            else:
                similarity += 5

            results.append(FunctionResult(str(function_id), similarity))

        return results

    def _install(self):
        try:
            from django.core.management import execute_from_command_line
        except ImportError:
            # The above import may fail for some other reason. Ensure that the
            # issue is really that Django is missing to avoid masking other
            # exceptions on Python 2.
            try:
                import django
            except ImportError:
                raise ImportError(
                    "Couldn't import Django. Are you sure it's installed and "
                    "available on your PYTHONPATH environment variable? Did you "
                    "forget to activate a virtual environment?"
                )
            raise
        execute_from_command_line(['manage.py', 'makemigrations', 'engines'])
        execute_from_command_line(['manage.py', 'migrate', 'engines'])

    def _uninstall(self):
        print('Manually delete tables associated with {}'.format(self.engine_name))
