#-------------------------------------------------------------------------------
#
#   FIRST Engine: Basic Masking
#   Author: Angel M. Villegas (anvilleg@cisco.com)
#   Last Modified: August 2017
#
#   Uses Capstone to obtain instructions and then removes certain instruction
#   details to normalize it into a standard form to be compared to other
#   functions.
#
#       Masks out:
#       -   ESP/EBP Offsets
#       -   Absolute Calls??
#       -   Global Offsets??
#
#   Requirements
#   ------------
#   -   Capstone
#
#   Installation
#   ------------
#   None
#
#-------------------------------------------------------------------------------

#   Python Modules
import re
from hashlib import sha256

#   FIRST Modules
from first_core.error import FIRSTError
from first_core.engines import AbstractEngine
from first_core.engines.results import FunctionResult

#   Third Party Modules
from capstone import *
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

MIN_REQUIRED_INSTRUCTIONS = 8

class BasicMasking(models.Model):
    sha256 = models.CharField(max_length=64)
    architecture = models.CharField(max_length=64)

    total_bytes = models.IntegerField()
    functions = models.ManyToManyField('BasicMaskingFunction')

    class Meta:
        app_label = 'engines'
        index_together = ('sha256', 'architecture')
        unique_together = ('sha256', 'architecture', 'total_bytes')

    def dump(self):
        return {'sha256' : self.sha256,
                'architecture' : self.architecture,
                'total_bytes' : self.total_bytes,
                'functions' : self.functions.all()}

class BasicMaskingFunction(models.Model):
    func = models.BigIntegerField()

    class Meta:
        app_label = 'engines'


class BasicMaskingEngine(AbstractEngine):
    _name = 'BasicMasking'
    _description = ('Masks calls/jmps offsets. Requires at least 8 instructions.')
    _required_db_names = ['first_db']

    def normalize(self, disassembly):
        if not disassembly:
            return (0, None)

        changed_bytes = 0

        try:
            normalized = []
            original = []
            for i in disassembly.instructions():
                original.append(str(i.bytes).encode('hex'))
                instr = ''.join(chr(x) for x in i.opcode if x)

                #   Special mnemonic masking (Call, Jmp, JCC)
                if disassembly.is_call(i) or disassembly.is_jump(i):
                    operand = i.op_str

                    if disassembly.is_op_imm(i.operands[0]):
                        changed_bytes += len(i.bytes) - len(instr)

                    #    TODO: Add capability to mask off stack reg for more
                    #           than Intel
                    #elif (disassembly.is_op_mem(i.operands[0])
                    #    and disassembly.is_stack_offset(i.operands[0])):
                    #    instr += i.reg_name(i.operands[0].value.reg)
                    #    #changed_bits += i.operands[0].dispSize
                    else:
                        instr += ''.join(chr(x) for x in i.bytes[len(instr):])

                    normalized.append(instr)
                    continue

                else:
                    normalized.append(str(i.bytes))

                '''
                #   Below code is from Distorm3 version
                #   TODO: Migrate to and understand how to accomplish in Capstone
                operand_instrs = []
                for operand_obj in i.operands:
                    #   TODO
                    #operand = operand_obj._toText()
                    if ((re.match('^\[E(S|B)P', operand) or re.match('^\[R(I|S)P', operand))
                        and operand_obj.dispSize):
                        #   Offset from EBP/ESP and RIP/RSP
                        masked = operand.replace(hex(operand_obj.disp), '0x')
                        operand_instrs.append(masked)
                        changed_bits += operand_obj.dispSize

                    elif 'Immediate' == operand_obj.type:
                        value = operand_obj.value
                        #   Masking off immediates within the standard VA of the sample
                        if ((0x400000 <= value <= 0x500000)
                            or (0x10000000 <= value <= 0x20000000)
                            or (0x1C0000000 <= value <= 0x1D0000000)
                            or (0x140000000 <= value <= 0x150000000)):
                            operand_instrs.append('0x')
                            changed_bits += operand_obj.size

                        else:
                            operand_instrs.append(operand)

                    elif 'AbsoluterMemoryAddress' == operand_obj.type:
                        operand_instrs.append('0x')
                        changed_bits += operand_obj.dispSize

                    elif 'AbsoluteMemory' == operand_obj.type:
                        masked = operand.replace(hex(operand_obj.disp), '0x')
                        operand_instrs.append(masked)
                        changed_bits += operand_obj.dispSize

                    else:
                        operand_instrs.append(operand)

                normalized.append(instr + ', '.join(operand_instrs))
            '''

            print 'Original'
            print original
            print 'Normalized'
            print [x.encode('hex') for x in normalized]

            if MIN_REQUIRED_INSTRUCTIONS > len(normalized):
                print 145
                return (0, None)

            h_sha256 = sha256(''.join(normalized)).hexdigest()
            print (changed_bytes, h_sha256)
            return (changed_bytes, h_sha256)

        except Exception as e:
            print 160, e

            return (0, None)

    def _add(self, function):
        '''
        Masks specific details from the disassembly to provide a fuzzy hash.
        '''
        opcodes_size = len(function['opcodes'])
        architecture = function['architecture']
        disassembly = function.get('disassembly')
        changed, h_sha256 = self.normalize(disassembly)

        if not h_sha256:
            return


        try:
            db_obj = BasicMasking.objects.get(sha256=h_sha256,
                                                architecture=architecture)
        except ObjectDoesNotExist:
            db_obj = BasicMasking.objects.create(sha256=h_sha256,
                                                    architecture=architecture,
                                                    total_bytes=opcodes_size)

        function_id = function['id']
        count = BasicMasking.objects.filter(sha256=h_sha256,
                                            architecture=architecture,
                                            functions__func=function_id).count()

        if not count:
            func, _ = BasicMaskingFunction.objects.get_or_create(func=function_id)
            db_obj.functions.add(func)

    def _scan(self, opcodes, architecture, apis, disassembly):
        '''Returns List of tuples (function ID, similarity percentage)'''
        db = self._dbs['first_db']
        changed, h_sha256 = self.normalize(disassembly)

        if not h_sha256:
            return

        try:
            db_obj = BasicMasking.objects.get(sha256=h_sha256,
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

            #   Similarity = 90% (opcodes and the masking changes)
            #                + 10% (api overlap)
            similarity = 100 - ((changed / (len(opcodes) * 8.0)) * 100)
            if similarity > 90.0:
                similarity = 90.0

            #   The APIs will count up to 10% of the similarity score
            total_apis = function.apis.count()
            if total_apis:
                func_apis = {x['api'] for x in function.apis.values('api')}
                overlap = float(len(func_apis.intersection(apis)))
                similarity += (overlap / total_apis) * 10

            results.append(FunctionResult(function_id, similarity))

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
        print 'Manually delete tables associated with {}'.format(self.engine_name)
