"""CPU functionality."""

import sys
from datetime import datetime

# Registers
IM   = 5 # R5 : Interrupt Mask
IS   = 6 # R6 : Interrupt Status
SP   = 7 # R7 : Stack Pointer
# Operations
ADD  = 0b10100000
CALL = 0b01010000
COMP = 0b10100111
DIV  = 0b10100011
HLT  = 0b00000001
INC  = 0b01100101
INTE = 0b01010010
IRET = 0b00010011
JEQ  = 0b01010101
JMP  = 0b01010100
JNE  = 0b01010110
LDI  = 0b10000010
MUL  = 0b10100010
NOP  = 0b00000000
PRA  = 0b01001000
POP  = 0b01000110
PRN  = 0b01000111
PUSH = 0b01000101
RET  = 0b00010001
ST   = 0b10000100

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.running = False
        self.interrupts_disabled = False
        self.last_time = datetime.now()
        # Set up internal registers
        self.pc  = 0 # Program Counter (PC)
        self.ir  = 0 # Instruction Register (IR)
        self.mar = 0 # Memory Address Register (MAR)
        self.mdr = 0 # Memory Data Register (MDR)
        self.fl  = 0 # Flags (FL)
        # Set up registers
        self.reg = [
            0,   # R0
            0,   # R1
            0,   # R2
            0,   # R3
            0,   # R4
            0,   # R5 : Interrupt Mask (IM)
            0,   # R6 : Interrupt Status (IS)
            0xF4 # R7 : Stack Pointer (SP)
        ]
        # Set up dispatch branch table
        self.dispatch = {
            ADD:  self.add,
            CALL: self.call,
            COMP: self.comp,
            DIV:  self.div,
            HLT:  self.hlt,
            INC:  self.inc,
            INTE: self.inte,
            IRET: self.iret,
            JEQ:  self.jeq,
            JMP:  self.jmp,
            JNE:  self.jne,
            LDI:  self.ldi,
            MUL:  self.mul,
            NOP:  self.nop,
            POP:  self.pop,
            PRA:  self.pra,
            PRN:  self.prn,
            PUSH: self.push,
            RET:  self.ret,
            ST:   self.st
        }


    def load(self):
        """Load a program into memory."""

        address = 0

        # If no file given, just hardcode a program:
        if len(sys.argv) == 1:
            program = [
                # From print8.ls8
                0b10000010, # LDI R0,8
                0b00000000,
                0b00001000,
                0b01000111, # PRN R0
                0b00000000,
                0b00000001, # HLT
            ]
        # If file given, load file
        elif len(sys.argv) == 2:
            try:
                program = []
                with open(sys.argv[1], "r") as f:
                    for line in f:
                        if len(line) > 1 and line[0] != "#":
                            program.append(int(line.split("#")[0].strip("\n"), 2))

            except FileNotFoundError:
                print(f"{sys.argv[0]}: could not find {sys.argv[1]}")
                sys.exit(2)
        else:
            print("Too many arguments given!")
            sys.exit(2)

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    ### START OF OPERATIONS ###
    def add(self):
        self.alu("ADD", self.ram_read(self.pc + 1), self.ram_read(self.pc + 2))
        self.pc += 3


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "DIV":
            if self.reg[reg_b] == 0:
                print("Error: Cannot divide by 0!")
                self.hlt()
            else:
                self.reg[reg_a] /= self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")


    def call(self):
        self.reg[SP] -= 1
        self.ram_write(self.reg[SP], self.pc + 2)
        self.pc = self.reg[self.ram_read(self.pc + 1)]


    def comp(self):
        """

        *This is an instruction handled by the ALU.*

        `CMP registerA registerB`

        Compare the values in two registers.

        * If they are equal, set the Equal `E` flag to 1, otherwise set it to 0.

        * If registerA is less than registerB, set the Less-than `L` flag to 1,
        otherwise set it to 0.

        * If registerA is greater than registerB, set the Greater-than `G` flag
        to 1, otherwise set it to 0.

        Machine code:
        ```
        10100111 00000aaa 00000bbb
        A7 0a 0b
        ```

        """
        registerA = self.reg[self.ram_read(self.pc + 1)]
        registerB = self.reg[self.ram_read(self.pc + 2)]

        if registerA == registerB:
            self.fl = 0b00000001
        elif registerA < registerB:
            self.fl = 0b00000100
        elif registerA > registerB:
            self.fl = 0b00000010

        self.pc += 3


    def div(self):
        self.alu("DIV", self.ram_read(self.pc + 1), self.ram_read(self.pc + 2))
        self.pc += 3


    def hlt(self):
        self.running = False


    def inc(self):
        # TODO
        pass


    def inte(self):
        # TODO
        pass


    def iret(self):
        # TODO: Return from an interrupt handler.
        # Registers R6-R0 are popped off the stack in that order.
        # The `FL` register is popped off the stack.
        # The return address is popped off the stack and stored in `PC`.
        # Interrupts are re-enabled.
        pass


    def jeq(self):
        """

        `JEQ register`

        If `equal` flag is set (true), jump to the address stored in the given register.

        Machine code:
        ```
        01010101 00000rrr
        55 0r
        ```

        """
        if self.fl & 0b00000001 == 1:
            self.pc = self.reg[self.ram_read(self.pc + 1)]
        else:
            self.pc += 2


    def jmp(self):
        """

        `JMP register`

        Jump to the address stored in the given register.

        Set the `PC` to the address stored in the given register.

        Machine code:
        ```
        01010100 00000rrr
        54 0r
        ```

        """
        self.pc = self.reg[self.ram_read(self.pc + 1)]


    def jne(self):
        """

        `JNE register`

        If `E` flag is clear (false, 0), jump to the address stored in the given
        register.

        Machine code:
        ```
        01010110 00000rrr
        56 0r
        ```

        """
        if self.fl & 0b00000001 == 0:
            self.pc = self.reg[self.ram_read(self.pc + 1)]
        else:
            self.pc += 2


    def ldi(self):
        self.reg[self.ram_read(self.pc + 1)] = self.ram_read(self.pc + 2)
        self.pc += 3


    def mul(self):
        # Multiply the values in two registers together and store the result in registerA.
        self.alu("MUL", self.ram_read(self.pc + 1), self.ram_read(self.pc + 2))
        self.pc += 3


    def nop(self):
        # No operation. Do nothing for this instruction.
        self.pc += 1


    def pop(self):
        self.reg[self.ram_read(self.pc + 1)] = self.ram_read(self.reg[SP])
        # No need to reset to 0 because push will overwrite later
        # self.ram[self.reg["SP"]] = 0
        self.reg[SP] += 1
        self.pc += 2
        return self.reg[self.ram_read(self.pc - 1)]


    def pra(self):
        """

        `PRA register` pseudo-instruction

        Print alpha character value stored in the given register.

        Print to the console the ASCII character corresponding to the value in the
        register.

        Machine code:
        ```
        01001000 00000rrr
        48 0r
        ```

        """

        print(chr(self.reg[self.ram_read(self.pc + 1)]))


    def prn(self):
        print(self.reg[self.ram_read(self.pc + 1)])
        self.pc += 2


    def push(self):
        self.reg[SP] -= 1
        self.ram_write(self.reg[SP], self.reg[self.ram_read(self.pc + 1)])
        self.pc += 2


    def ret(self):
        self.pc = self.ram_read(self.reg[SP])
        self.ram_write(self.reg[SP], 0)
        self.reg[SP] += 1
    
    
    def st(self):
        """

        `ST registerA registerB`

        Store value in registerB in the address stored in registerA.

        This opcode writes to memory.

        Machine code:
        ```
        10000100 00000aaa 00000bbb
        84 0a 0b
        ```

        """
        self.ram_write(self.reg[self.ram_read(self.pc + 1)], self.reg[self.ram_read(self.pc + 2)])
        self.pc += 3
    
    ### END OF OPERATIONS ###

    def check_timer_interrupt(self):
        if self.reg[IM]:
            pass



    def check_keyboard_interrupt(self):
        pass


    def ram_read(self, mar):
        return self.ram[mar]


    def ram_write(self, mar, mdr):
        self.ram[mar] = mdr


    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X | %02X %02X %02X |" % (
            self.pc,
            self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        self.running = True

        while self.running:
            if self.interrupts_disabled == False and self.reg[IM] & 0b00000001:
                now = datetime.now()
                if (now - self.last_time).seconds >= 1:
                    self.reg[IS] = 1
                    maskedInterrupts = self.reg[IM] & self.reg[IS]
                    for idx in range(len(bin(maskedInterrupts)) - 2):
                        if bin(maskedInterrupts)[::-1][idx] == "1":
                            self.interrupts_disabled = True
                            self.reg[IS] = 0
                            # Push `PC` register to stack
                            self.reg[SP] -= 1
                            self.ram_write(self.reg[SP], self.pc)
                            # Push `FL` register to stack
                            self.reg[SP] -= 1
                            self.ram_write(self.reg[SP], self.fl)
                            for register in self.reg[:6]:
                                # Push R0-R6 to stack in that order
                                self.reg[SP] -= 1
                                self.ram_write(self.reg[SP], register)
                            self.pc = self.ram_read(0xF8)
                            self.last_time = now
                            break
            self.dispatch[self.ram[self.pc]]()
