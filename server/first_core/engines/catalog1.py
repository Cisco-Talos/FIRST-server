#-------------------------------------------------------------------------------
#
#   FIRST Engine: Catalog1
#   Author: Andrea Marcelli (anmarcel@cisco.com)
#   Last Modified: July 2019
#
#   This engine uses the catalog1 sensitive
#   hashing algorithm by xorpd.
#
#   For more information:
#   https://www.xorpd.net/pages/fcatalog.html
#   https://github.com/xorpd/fcatalog_server/
#
#   Requirements
#   ------------
#   None
#
#   Installation
#   ------------
#   None
#
#-------------------------------------------------------------------------------

#   Python Modules
import json
import base64
from hashlib import sha256
from collections import Counter

# Catalog1lib
from .catalog1lib import slow_sign

#   FIRST Modules
from first_core.error import FIRSTError
from first_core.engines import AbstractEngine
from first_core.engines.results import FunctionResult

#   Third Party Modules
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

NUM_PERMS = 64
MATCH_THRESHOLD = 80

class Catalog1(models.Model):
    sha256 = models.CharField(max_length=64)
    architecture = models.CharField(max_length=64)
    functions = models.ManyToManyField('Catalog1Functions')
    catalog1hashes = models.ManyToManyField('Catalog1Hash')

    class Meta:
        app_label = 'engines'
        index_together = ('sha256', 'architecture')
        unique_together = ('sha256', 'architecture')

    def dump(self):
        return {'sha256': self.sha256,
                'architecture': self.architecture,
                'functions': self.functions.all(),
                'catalog1hashes': self.catalog1hashes.all()}


class Catalog1Hash(models.Model):
    catalog_hash = models.CharField(max_length=32)

    class Meta:
        app_label = 'engines'


class Catalog1Functions(models.Model):
    func = models.BigIntegerField()

    class Meta:
        app_label = 'engines'


class Catalog1Engine(AbstractEngine):
    _name = 'Catalog1'
    _description = 'catalog1 sensitive hashing algorithm by xorpd'
    _required_db_names = ['first_db']

    def _add(self, function):
        '''
        Get the list of hashes from fcatalog
        '''
        architecture = function['architecture']
        opcodes = function["opcodes"]
        function_id = function['id']

        if len(opcodes) < 4:
            # Minum opcodes lenght: 4
            print("Catalog1 log: opcodes len < minimum (4)")
            return

        catalog1hashes = slow_sign(opcodes, NUM_PERMS)
        # join the sorted list of hashes, and calculate the sha256
        # This creates an unique identifier of the fuzzy hash
        catalog1_string = ''.join([str(x) for x in sorted(catalog1hashes)])
        catalog1_sha256 = sha256(catalog1_string.encode('utf-8')).hexdigest()

        count = Catalog1.objects.filter(sha256=catalog1_sha256,
                                        architecture=architecture,
                                        functions__func=function_id).count()
        if not count:
            # Create a new database object

            db_obj, _ = Catalog1.objects.get_or_create(sha256=catalog1_sha256,
                                                       architecture=architecture)
            # Add the function to the db_obj
            func, _ = Catalog1Functions.objects.get_or_create(func=function_id)
            db_obj.functions.add(func)

            # Add catalog hashes to the db_obj
            for ch in catalog1hashes:
                c_hash_obj, _ = Catalog1Hash.objects.get_or_create(
                    catalog_hash=ch)
                db_obj.catalog1hashes.add(c_hash_obj)

    def _scan(self, opcodes, architecture, apis, disassembly):
        '''
        Returns List of FunctionResults
        '''
        db = self._dbs['first_db']
        catalog1hashes = slow_sign(opcodes, NUM_PERMS)
        catalog1_string = ''.join([str(x) for x in sorted(catalog1hashes)])
        catalog1_sha256 = sha256(catalog1_string.encode('utf-8')).hexdigest()
        result = list()

        # Step 0: Let's try to see if the same catalog1_sha256 exists:
        try:
            db_obj = Catalog1.objects.get(sha256=catalog1_sha256, architecture=architecture)
            if db_obj:
                for f in db_obj.functions.all():
                    similarity = 100.0
                    function_id = f.func
                    function = db.find_function(_id=function_id)
                    if function:
                        result.append(FunctionResult(
                            str(function_id), similarity))
                return result

        except ObjectDoesNotExist:
            # No luck
            # Let's search
            pass

        # Step 1: Let's search all the matching catalog1 hashes
        matching_catalog_functions = Catalog1.objects.filter(architecture=architecture, catalog1hashes__catalog_hash__in=catalog1hashes).values_list('functions', flat=True)
        matching_function_columns = Catalog1Functions.objects.filter(id__in=matching_catalog_functions)

        matching_function_ids = {}
        for func_column in matching_function_columns:
            matching_function_ids[func_column.id] = func_column.func

        cc = Counter(matching_catalog_functions)
        for func_m_id, counter in cc.most_common(10):
            if counter > 0:
                function_id = matching_function_ids[func_m_id]
                similarity = counter * 100 / NUM_PERMS

                if similarity > MATCH_THRESHOLD:
                    result.append(FunctionResult(str(function_id), similarity))

        return result

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
