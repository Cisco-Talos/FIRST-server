#   Third Party Modules
from capstone import *
from capstone.ppc import *
from capstone.systemz import *
from capstone.arm import *
from capstone.arm64 import *
from capstone.x86 import *
from capstone.sparc import *
from capstone.mips import *

arch_mapping = {
    'ppc' : (CS_ARCH_PPC, CS_MODE_32),
    'ppc32' : (CS_ARCH_PPC, CS_MODE_32),
    'ppc64' : (CS_ARCH_PPC, CS_MODE_64),
    'intel16' : (CS_ARCH_X86, CS_MODE_16),
    'sysz' : (CS_ARCH_SYSZ, None),
    'arm32' : (CS_ARCH_ARM, CS_MODE_ARM),
    'intel32' : (CS_ARCH_X86, CS_MODE_ARM),
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
            self.md.details = True
            self.iterator = self.md.disasm(self.code, 0)
            self.valid = True

    def instructions(self):
        #   When first called function will return cached instructions
        for i in xrange(len(self.data)):
            yield self.data[i]

        #   Then iterate through non-cached instructions
        if not self.iterator:
            for i in self.iterator:
                self.data.append(i)
                yield i

            self.iterator = None

    def _check_mapping(self, mapping, operand):
        if ((not hasattr(operand, 'type'))
        or (self.architecture not in mapping)):
            False

        return operand.type == mapping[self.architecture]

    def is_op_reg(self, operand):
        return self._check_mapping(reg_mapping, operand)

    def is_op_mem(self, operand):
        return self._check_mapping(mem_mapping, operand)

    def is_op_imm(self, operand):
        return self._check_mapping(imm_mapping, operand)

    def is_op_invalid(self, operand):
        return self._check_mapping(invalid_mapping, operand)
