#-------------------------------------------------------------------------------
#
#   FIRST Engine: Catalog1
#   Author: Andrea Marcelli (anmarcel@cisco.com)
#   Last Modified: June 2019
#
#   This is a pure python implementation of the
#   catalog1 sensitive hashing algorithm by xorpd
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

#   FIRST Modules
from first_core.error import FIRSTError
from first_core.engines import AbstractEngine
from first_core.engines.results import FunctionResult

#   Third Party Modules
from django.db import models
from django.core.exceptions import ObjectDoesNotExist


WORD_SIZE = 32      # 32 bits.
MAX_WORD = (1 << WORD_SIZE) - 1

BYTE_SIZE = 8       # 8 bits.
NUM_ITERS = 4

RAND_DWORDS = [1445200656, 3877429363, 1060188777, 4260769784, 1438562000,
               2836098482, 1986405151, 4230168452, 380326093, 2859127666,
               1134102609, 788546250, 3705417527, 1779868252, 1958737986,
               4046915967, 1614805928, 4160312724, 3682325739, 534901034,
               2287240917, 2677201636, 71025852, 1171752314, 47956297,
               2265969327, 2865804126, 1364027301, 2267528752, 1998395705,
               576397983, 636085149, 3876141063, 1131266725, 3949079092,
               1674557074, 2566739348, 3782985982, 2164386649, 550438955,
               2491039847, 2409394861, 3757073140, 3509849961, 3972853470,
               1377009785, 2164834118, 820549672, 2867309379, 1454756115,
               94270429, 2974978638, 2915205038, 1887247447, 3641720023,
               4292314015, 702694146, 1808155309, 95993403, 1529688311,
               2883286160, 1410658736, 3225014055, 1903093988, 2049895643,
               476880516, 3241604078, 3709326844, 2531992854, 265580822,
               2920230147, 4294230868, 408106067, 3683123785, 1782150222,
               3876124798, 3400886112, 1837386661, 664033147, 3948403539,
               3572529266, 4084780068, 691101764, 1191456665, 3559651142,
               709364116, 3999544719, 189208547, 3851247656, 69124994,
               1685591380, 1312437435, 2316872331, 1466758250, 1979107610,
               2611873442, 80372344, 1251839752, 2716578101, 176193185,
               2142192370, 1179562050, 1290470544, 1957198791, 1435943450,
               2989992875, 3703466909, 1302678442, 3343948619, 3762772165,
               1438266632, 1761719790, 3668101852, 1283600006, 671544087,
               1665876818, 3645433092, 3760380605, 3802664867, 1635015896,
               1060356828, 1666255066, 2953295653, 2827859377, 386702151,
               3372348076, 4248620909, 2259505262]

NUM_PERMS = 64


def ror(x, i):
    """
    Rotate right x by i locations.
    x is a dword
    """
    # Make sure that i is in range:
    return ((x >> i) | (x << (WORD_SIZE - i))) & MAX_WORD


def perm(num, x):
    """
    A permutation from dwords to dwords.
    Implementation here is pretty arbitrary, and could be changed a bit if
    needed.
    num is the number of permutation (This could generate many different
    permutation functions)
    x is the input dword.
    """
    for i in range(NUM_ITERS):
        x += RAND_DWORDS[(i + num + x) % len(RAND_DWORDS)]
        x &= MAX_WORD
        ror_index = (x ^ RAND_DWORDS[(i + num + 1) % len(RAND_DWORDS)]) % \
            WORD_SIZE
        x = ror(x, ror_index)
        x ^= RAND_DWORDS[(i + num + x) % len(RAND_DWORDS)]
        ror_index = (x ^ RAND_DWORDS[(i + num + 1) % len(RAND_DWORDS)]) % \
            WORD_SIZE
        x = ror(x, ror_index)
        assert (x <= MAX_WORD) and (x >= 0)
    return x


def bytes_to_num(data):
    """
    Convert a string to a number
    """
    return int.from_bytes(bytes=data, byteorder='big')


def slow_sign(data, num_perms):
    """
    Sign over data.
    Use num_perms permutations. (The more you have, the more sensitive is the
    comparison later).
    """
    nbytes = WORD_SIZE // BYTE_SIZE
    if len(data) < nbytes:
        raise Exception('data must be at least of size {} bytes.'
                        .format(nbytes))

    res_sign = []

    for p in range(num_perms):
        num_iters = len(data) - nbytes + 1
        cur_sign = min([perm(p, bytes_to_num(data[i:i + nbytes])) for i in
                        range(num_iters)])
        res_sign.append(cur_sign)

    return res_sign


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
            db_obj = Catalog1.objects.get(sha256=catalog1_sha256,
                                          architecture=architecture)
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
        matching_function_ids = list()
        for ch in catalog1hashes:
            try:
                db_obj = Catalog1.objects.get(catalog1hashes__catalog_hash=ch,
                                              architecture=architecture)
                for f in db_obj.functions.all():
                    matching_function_ids.append(f.func)
            except ObjectDoesNotExist:
                pass

        cc = Counter(matching_function_ids)
        for function_id, counter in cc.most_common(10):
            if counter > 0:
                similarity = counter * 100 / NUM_PERMS
                print("Catalog1 log: %d %f" % (function_id, similarity))
                result.append(FunctionResult(str(function_id), similarity))
                break

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
