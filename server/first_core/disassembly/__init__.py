#   Third Party Modules

from capstone import CS_MODE_32
from capstone import CS_MODE_64
from capstone import CS_MODE_16

from capstone.ppc import CS_ARCH_PPC
from capstone.ppc import PPC_OP_REG
from capstone.ppc import PPC_OP_IMM
from capstone.ppc import PPC_OP_MEM
from capstone.ppc import PPC_OP_INVALID

from capstone.x86 import CS_ARCH_X86
from capstone.x86 import X86_OP_REG
from capstone.x86 import X86_OP_IMM
from capstone.x86 import X86_OP_MEM
from capstone.x86 import X86_OP_INVALID
from capstone.x86 import X86_INS_CALL
from capstone.x86 import X86_INS_JA
from capstone.x86 import X86_INS_JAE
from capstone.x86 import X86_INS_JB
from capstone.x86 import X86_INS_JBE
from capstone.x86 import X86_INS_JCXZ
from capstone.x86 import X86_INS_JE
from capstone.x86 import X86_INS_JECXZ
from capstone.x86 import X86_INS_JG
from capstone.x86 import X86_INS_JGE
from capstone.x86 import X86_INS_JL
from capstone.x86 import X86_INS_JLE
from capstone.x86 import X86_INS_JMP
from capstone.x86 import X86_INS_JNE
from capstone.x86 import X86_INS_JNO
from capstone.x86 import X86_INS_JNP
from capstone.x86 import X86_INS_JNS
from capstone.x86 import X86_INS_JO
from capstone.x86 import X86_INS_JP
from capstone.x86 import X86_INS_JRCXZ
from capstone.x86 import X86_INS_JS
from capstone.x86 import X86_INS_LJMP
from capstone.x86 import X86_REG_SP
from capstone.x86 import X86_REG_EBP
from capstone.x86 import X86_REG_ESP
from capstone.x86 import X86_REG_RSP

from capstone.systemz import CS_ARCH_SYSZ
from capstone.systemz import SYSZ_OP_REG
from capstone.systemz import SYSZ_OP_IMM
from capstone.systemz import SYSZ_OP_MEM
from capstone.systemz import SYSZ_OP_INVALID

from capstone.arm import CS_ARCH_ARM
from capstone.arm import CS_MODE_ARM
from capstone.arm import CS_ARCH_ARM64
from capstone.arm import ARM_OP_REG
from capstone.arm import ARM_OP_IMM
from capstone.arm import ARM_OP_MEM
from capstone.arm import ARM_OP_INVALID
from capstone.arm import ARM64_OP_REG
from capstone.arm import ARM64_OP_IMM
from capstone.arm import ARM64_OP_MEM
from capstone.arm import ARM64_OP_INVALID

from capstone.sparc import CS_ARCH_SPARC
from capstone.sparc import SPARC_OP_IMM
from capstone.sparc import SPARC_OP_REG
from capstone.sparc import SPARC_OP_MEM
from capstone.sparc import SPARC_OP_INVALID

from capstone.mips import CS_ARCH_MIPS
from capstone.mips import MIPS_OP_REG
from capstone.mips import MIPS_OP_IMM
from capstone.mips import MIPS_OP_MEM
from capstone.mips import MIPS_OP_INVALID


arch_mapping = {
    'ppc' : (CS_ARCH_PPC, CS_MODE_32),
    'ppc32' : (CS_ARCH_PPC, CS_MODE_32),
    'ppc64' : (CS_ARCH_PPC, CS_MODE_64),
    'intel16' : (CS_ARCH_X86, CS_MODE_16),
    'sysz' : (CS_ARCH_SYSZ, None),
    'arm32' : (CS_ARCH_ARM, CS_MODE_ARM),
    'intel32' : (CS_ARCH_X86, CS_MODE_32),
    'intel64' : (CS_ARCH_X86, CS_MODE_64),
    'sparc' : (CS_ARCH_SPARC, None),
    'arm64' : (CS_ARCH_ARM64, CS_MODE_ARM),
    'mips' : (CS_ARCH_MIPS, CS_MODE_32),
    'mips64' : (CS_ARCH_MIPS, CS_MODE_64)
}

reg_mapping = {
    'ppc' :  PPC_OP_REG, 'ppc32' : PPC_OP_REG, 'ppc64' : PPC_OP_REG,
    'sysz' : SYSZ_OP_REG,
    'intel16' : X86_OP_REG, 'intel32' : X86_OP_REG, 'intel64' : X86_OP_REG,
    'sparc' : SPARC_OP_REG,
    'arm32' : ARM_OP_REG, 'arm64' : ARM64_OP_REG,
    'mips' : MIPS_OP_REG, 'mips64' : MIPS_OP_REG
}

imm_mapping = {
    'ppc' :  PPC_OP_IMM, 'ppc32' : PPC_OP_IMM, 'ppc64' : PPC_OP_IMM,
    'sysz' : SYSZ_OP_IMM,
    'intel16' : X86_OP_IMM, 'intel32' : X86_OP_IMM, 'intel64' : X86_OP_IMM,
    'sparc' : SPARC_OP_IMM,
    'arm32' : ARM_OP_IMM, 'arm64' : ARM64_OP_IMM,
    'mips' : MIPS_OP_IMM, 'mips64' : MIPS_OP_IMM
}

mem_mapping = {
    'ppc' :  PPC_OP_MEM, 'ppc32' : PPC_OP_MEM, 'ppc64' : PPC_OP_MEM,
    'sysz' : SYSZ_OP_MEM,
    'intel16' : X86_OP_MEM, 'intel32' : X86_OP_MEM, 'intel64' : X86_OP_MEM,
    'sparc' : SPARC_OP_MEM,
    'arm32' : ARM_OP_MEM, 'arm64' : ARM64_OP_MEM,
    'mips' : MIPS_OP_MEM, 'mips64' : MIPS_OP_MEM
}

invalid_mapping = {
    'ppc' :  PPC_OP_INVALID, 'ppc32' : PPC_OP_INVALID, 'ppc64' : PPC_OP_INVALID,
    'sysz' : SYSZ_OP_INVALID,
    'intel16' : X86_OP_INVALID, 'intel32' : X86_OP_INVALID, 'intel64' : X86_OP_INVALID,
    'sparc' : SPARC_OP_INVALID,
    'arm32' : ARM_OP_INVALID, 'arm64' : ARM64_OP_INVALID,
    'mips' : MIPS_OP_INVALID, 'mips64' : MIPS_OP_INVALID
}

_call_mapping = {
    'ppc' : [],
    'sysz' : [],
    'x86' : [X86_INS_CALL],
    'sysz' : [],
    'sparc' : [],
    'arm' : [],
    'arm64' : [],
    'mips' : []
}
call_mapping = {
    'ppc' :  _call_mapping['ppc'],
    'ppc32' : _call_mapping['ppc'],
    'ppc64' : _call_mapping['ppc'],
    'sysz' : _call_mapping['sysz'],
    'intel16' : _call_mapping['x86'],
    'intel32' : _call_mapping['x86'],
    'intel64' : _call_mapping['x86'],
    'sparc' : _call_mapping['sparc'],
    'arm32' : _call_mapping['arm'], 'arm64' : _call_mapping['arm64'],
    'mips' : _call_mapping['mips'], 'mips64' : _call_mapping['mips']
}

_jump_mapping = {
    'x86' : [   X86_INS_JA, X86_INS_JAE, X86_INS_JB, X86_INS_JBE, X86_INS_JCXZ,
                X86_INS_JE, X86_INS_JECXZ, X86_INS_JG, X86_INS_JGE, X86_INS_JL,
                X86_INS_JLE, X86_INS_JMP, X86_INS_JNE, X86_INS_JNO, X86_INS_JNP,
                X86_INS_JNS, X86_INS_JO, X86_INS_JP, X86_INS_JRCXZ, X86_INS_JS,
                X86_INS_LJMP]
}
jump_mapping = {
    'intel16' : _jump_mapping['x86'],
    'intel32' : _jump_mapping['x86'],
    'intel64' : _jump_mapping['x86']
}

stack_offsets = {
    'intel16' : [X86_REG_SP],
    'intel32' : [X86_REG_EBP, X86_REG_ESP],
    'intel64' : [X86_REG_RSP]
}


class Disassembly(object):
    def __init__(self, architecture, code):
        self.md = None
        self.data = []
        self.code = code
        self.iterator = None
        self.architecture = architecture

        self.valid = False

        if architecture in arch_mapping:
            arch, mode = arch_mapping[architecture]
            self.md = Cs(arch, mode)
            self.md.detail = True
            self.iterator = self.md.disasm(self.code, 0)
            self.valid = True



    def instructions(self):
        #   When first called function will return cached instructions
        for i in range(len(self.data)):
            yield self.data[i]

        #   Then iterate through non-cached instructions
        if self.iterator:
            for i in self.iterator:
                self.data.append(i)
                yield i

            self.iterator = None


    def _check_mapping(self, mapping, operand, attr='type', equal=True):
        if ((not hasattr(operand, attr))
        or (self.architecture not in mapping)):
            False

        if equal:
            return getattr(operand, attr) == mapping[self.architecture]

        return getattr(operand, attr) in mapping[self.architecture]

    #   Operand Related Functionality
    def is_op_reg(self, operand):
        return self._check_mapping(reg_mapping, operand)

    def is_op_mem(self, operand):
        return self._check_mapping(mem_mapping, operand)

    def is_op_imm(self, operand):
        return self._check_mapping(imm_mapping, operand)

    def is_op_invalid(self, operand):
        return self._check_mapping(invalid_mapping, operand)

    def is_stack_offset(self, operand):
        if not hasattr(operand, 'mem'):
            return False
        return self._check_mapping(stack_offsets, operand.mem, 'base', False)


    #   Instruction Related functionality
    def is_call(self, instr):
        return self._check_mapping(call_mapping, instr, 'id', False)

    def is_jump(self, instr):
        return self._check_mapping(jump_mapping, instr, 'id', False)
