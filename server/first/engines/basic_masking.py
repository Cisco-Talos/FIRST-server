#-------------------------------------------------------------------------------
#
#   FIRST Engine: Basic Masking
#   Author: Angel M. Villegas (anvilleg@cisco.com)
#   Last Modified: March 2016
#
#   Uses Distorm3 to obtain instructions and then removes certain instruction
#   details to normalize it into a standard form to be compared to other
#   functions.
#
#       Maskes out:
#       -   ESP/EBP Offsets
#       -   Absolute Calls??
#       -   Global Offsets??
#
#   Requirements
#   ------------
#   -   Distorm3
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
from first.error import FIRSTError
from first.engines import AbstractEngine
from first.engines.results import FunctionResult

#   Third Party Modules
from bson.objectid import ObjectId
from distorm3 import DecomposeGenerator, Decode32Bits, Decode64Bits, Decode16Bits
from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine import Document, StringField, ListField, IntField, \
                        ObjectIdField

class BasicMasking(Document):
    sha256 = StringField(max_length=64, required=True)
    architecture = StringField(max_length=64, required=True)
    instructions = ListField(StringField(max_length=124), required=True)
    total_bytes = IntField(required=True, default=0)
    functions = ListField(ObjectIdField(), default=list)

    meta = {
        'indexes' : [('sha256', 'architecture', 'instructions')]
    }

    def dump(self):
        return {'sha256' : self.sha256,
                'architecture' : self.architecture,
                'instructions' : self.instructions,
                'total_bytes' : self.total_bytes,
                'functions' : self.function_list()}

    def function_list(self):
        return [str(x) for x in self.functions]


class BasicMaskingEngine(AbstractEngine):
    _name = 'BasicMasking'
    _description = ('Masks ESP/EBP offsets, calls/jmps offsets, and global '
                    'offsets (Intel Only). Requires at least 8 instructions.')
    _required_db_names = ['first_db']

    def normalize(self, opcodes, architecture):
        changed_bits = 0
        dt = None
        mapping = {'intel32' : Decode32Bits,
                    'intel64' : Decode64Bits,
                    'intel16' : Decode16Bits}
        if architecture in mapping:
            dt = mapping[architecture]
        else:
            return (None, changed_bits, None)
            
        try:
            normalized = []
            original = []
            for i in DecomposeGenerator(0, opcodes, dt):
                #   If disassembly is not valid then junk data has been sent
                if not i.valid:
                    return (None, 0, None)

                original.append(i._toText())
                instr = i.mnemonic + ' '

                #   Special mnemonic masking (Call, Jmp, JCC)
                if (i.mnemonic == 'CALL') or i.mnemonic.startswith('J'):
                    operand = i.operands[0]._toText()

                    if 'Immediate' == i.operands[0].type:
                        instr += '0x'
                        changed_bits += i.operands[0].size

                    else:
                        regex = '^\[R(S|I)P(\+|\-)0x[\da-f]+\]$'
                        if re.match(regex, operand):
                            instr += re.sub(regex, r'[R\1P\2', operand) + '0x]'
                            changed_bits += i.operands[0].dispSize
                        else:
                            #   Nothing will be masked out
                            instr = i._toText()

                    normalized.append(instr)
                    continue

                operand_instrs = []
                for operand_obj in i.operands:
                    operand = operand_obj._toText()
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

            h_sha256 = sha256(''.join(normalized)).hexdigest()
            return (normalized, changed_bits, h_sha256)
            #   For debugging
            #return (original, normalized, changed_bits, h_sha256)

        except Exception as e:
            return (None, changed_bits, None)

    def _add(self, function):
        '''

        '''
        opcodes = function['opcodes']
        architecture = function['architecture']
        normalized, changed, h_sha256 = self.normalize(opcodes, architecture)

        if (not h_sha256) or (not normalized) or (8 > len(normalized)):
            return

        try:
            db_obj = BasicMasking.objects(  sha256=h_sha256,
                                            architecture=architecture,
                                            instructions=normalized).get()
        except DoesNotExist:
            db_obj = BasicMasking(  sha256=h_sha256,
                                    architecture=architecture,
                                    instructions=normalized,
                                    total_bytes=len(opcodes))

        function_id = ObjectId(function['id'])
        if function_id not in db_obj.functions:
            db_obj.functions.append(function_id)
            db_obj.save()

    def _scan(self, opcodes, architecture, apis):
        '''Returns List of tuples (function ID, similarity percentage)'''
        db = self._dbs['first_db']
        normalized, changed, h_sha256 = self.normalize(opcodes, architecture)

        if (not h_sha256) or (not normalized) or (8 > len(normalized)):
            return

        try:
            db_obj = BasicMasking.objects(  sha256=h_sha256,
                                            architecture=architecture,
                                            instructions=normalized).get()
        except DoesNotExist:
            return None

        results = []
        for function_id in db_obj.function_list():
            function = db.find_function(_id=ObjectId(function_id))

            if not function or not function.metadata:
                continue

            #   Similarity = 90% (opcodes and the masking changes)
            #                + 10% (api overlap)
            similarity = 100 - ((changed / (len(opcodes) * 8.0)) * 100)
            if similarity > 90.0:
                similarity = 90.0

            #   The APIs will count up to 10% of the similarity score
            total_apis = len(function.apis)
            overlap = float(len(set(function.apis).intersection(apis)))
            if 0 != total_apis:
                similarity += (overlap / total_apis) * 10

            results.append(FunctionResult(function_id, similarity))

        return results

    def _uninstall(self):
        BasicMasking.drop_collection()
