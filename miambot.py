import string
import struct

from miasm.arch.ia32_arch import *

from pypeul import *

IRC_SERVER = "..."


def pad(s):
    return "0" * (2 - len(s)) + s


def isHexa(s):
    for c in s:
        if not c in string.hexdigits:
            return False
    return True


class MiamBot(IRC):
    def __init__(self):
        IRC.__init__(self)

    def on_ready(self):
        self.join('#revolution')

    def on_channel_message(self, umask, target, msg):
        try:
            if msg == '!help' or msg == '!h':
                self.message(target, "MiamBot - Help")
                self.message(target, "--------")
                self.message(target, "    Assemble")
                self.message(target, "	      x86     : !a | !a86")
                self.message(target, "	      ppc     : !appc")
                self.message(target, "    Disassemble")
                self.message(target, "	      x86     : !d | !d86")
                self.message(target, "	      ppc     : !dppc")
                self.message(target, "--------")
            if msg.startswith('!appc '):
                instrs = msg[msg.find(' '):].split(";")
                res = ""
                for instr in instrs:
                    instr = instr.encode('ascii', 'ignore').strip().upper()
                    if len(instr) == 0:
                        continue
                    op1 = ppc_mn.asm(instr)[0]
                    h = struct.unpack('>L', op1)
                    strH = "%.8x" % h
                    for i in [0, 2, 4, 6]:
                        res += "\\x" + strH[i:i + 2].lower()
                self.message(target, res)
            if msg.startswith('!dppc '):
                asms = msg[msg.find(' '):].replace("\\x", "").replace("0x", "").replace(' ', '').encode('ascii',
                                                                                                        'ignore').strip().upper()
                if not isHexa(asms):
                    raise Exception, "Input contains non hexadecimal character"
                if len(asms) % 2 == 1 or len(asms) % 8 != 0:
                    raise Exception, "Check input length"
                i = 0
                disass = ""
                while i < len(asms):
                    hStr = asms[i:i + 8].decode('hex')
                    instr = ppc_mn.dis(hStr)
                    disass += str(instr).strip() + "\n"
                    i += 8
                self.message(target, disass.strip())
            if msg.startswith('!a ') or msg.startswith('!a86 '):
                instrs = msg[msg.find(' '):].split(";")
                res = ""
                for instr in instrs:
                    instr = instr.encode('ascii', 'ignore').strip()
                    if len(instr) == 0:
                        continue
                    l = x86_mn.asm(instr)
                    if l == None or len(l) == 0:
                        if res != "":
                            self.message(target, res)
                        raise Exception, "Can not assemble " + instr
                    l = l[0]
                    if l == "@":
                        l = l[1]
                    for b in l:
                        res += "\\x" + pad(hex(ord(b))[2:])
                self.message(target, res)
            elif msg.startswith('!d ') or msg.startswith('!d86 '):
                asms = msg[msg.find(' '):].replace("\\x", "").replace("0x", "").replace(' ', '').encode('ascii',
                                                                                                        'ignore').strip()
                if not isHexa(asms):
                    raise Exception, "Input contains non hexadecimal character"
                if len(asms) % 2 == 1:
                    raise Exception, "Check input length"
                i = 0
                disass = ""
                while i < len(asms):
                    instr = x86_mn.dis(asms[i:].decode('hex'))
                    disass += str(instr).strip() + "\n"
                    i += instr.l * 2
                self.message(target, disass.strip())
        except AttributeError:
            self.message(target, Tags.Bold('Exception : ') + "Not enought bytes")
        except Exception, ex:
            if str(ex).find('x not in list') > 0:
                self.message(target, Tags.Bold('Exception : ') + 'A symbol is not in PPC asm')
            elif str(ex).find('ambiquity') > 0:
                self.message(target, Tags.Bold('Exception : ') + 'Ambuiguous instruction')
            else:
                self.message(target, Tags.Bold('Exception : ') + str(ex))


bot = MiamBot()
bot.connect(IRC_SERVER, 6697, True)
bot.ident('miambot')
bot.run()
