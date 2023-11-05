import pygame
from time import sleep

gridcolor = (76, 45, 28)
offcolor = (173, 101, 62)
oncolor = (242, 201, 159)

pygame.init()

grid_size = (32, 16)
cell_size = 40
window_size = (grid_size[0] * cell_size, grid_size[1] * cell_size)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Incel2's output display")


def draw_pixel(pixel, on=True):
    x, y = pixel
    rect = pygame.Rect(x * cell_size, (grid_size[1] - y - 1) * cell_size, cell_size, cell_size)
    pygame.draw.rect(screen, oncolor if on else offcolor, rect)
    pygame.draw.rect(screen, gridcolor, rect, 1)


def draw_grid():
    for x in range(grid_size[0]):
        for y in range(grid_size[1]):
            draw_pixel((x, y), False)


draw_grid()


def emulate(file_name, debug=True, display=False):

    if not display:
        pygame.quit()

    global oncolor
    num_regs = 8
    num_flags = 4
    num_ports = 7
    ram_size = 64
    rom_size = 256
    cpu_bits = 8
    opcodes = [
        "NOOP",
        "ADD",
        "SUB",
        "AND",
        "OR",
        "ADC",
        "RSH",
        "ADI",
        "ANDI",
        "XORI",
        "LDI",
        "MST",
        "MLD",
        "PST",
        "PLD",
        "BRC",
        "JMP",
        "JAL",
        "HLT"
    ]

    registers: list[int] = [0] * num_regs
    flags = [False] * num_flags
    ram = [0] * ram_size
    rom = [""] * rom_size
    stack = []
    portsI = [0] * num_ports
    portsO = [0] * num_ports
    pc: int = 0

    with open(file_name, "r") as lines:
        try:
            for index, value in enumerate(lines.read().splitlines()):
                rom[index] = value
        except IndexError:
            print('Rom full! Make sure to have a maximum of 256 lines.')
            exit()

    running = True
    cycles = 0
    labels = {}

    for i in range(len(rom)):
        instruction = rom[i]
        instruction = list(instruction.split(" "))
        if instruction[0].startswith("["):
            labels[instruction[0]] = i

    old_port_0 = ""
    old_port_1 = ""

    while running:

        instruction = rom[pc]
        instruction = list(instruction.split(" "))
        registers[0] = 0
        regs = []
        opcode = ""
        regDest = ""
        regA = ""
        regB = ""
        port = ""
        pop = ""
        value = ""
        flag = ""
        label = ""
        immediate = ""

        for i in range(len(instruction)):
            if instruction[i].startswith("["):
                labels[instruction[0]] = pc
            elif instruction[i] in opcodes:
                opcode = instruction[i]
            elif instruction[i].startswith("R"):
                if instruction[i][1].isdigit():
                    regs.append(int(instruction[i][1::]))
                else:
                    print(f"Error at line {pc}: invalid value after a R")
                    exit()
            elif instruction[i].startswith("P"):
                if opcode == "PST" or opcode == "PLD":
                    if instruction[i][1] in ("0", "1", "2", "3", "4", "5", "6", "7"):
                        port = int(instruction[i][1::])
                    else:
                        print(f"Error at line {pc}: invalid value after a P")
                        exit()
                elif opcode == "JMP":
                    if instruction[i][1] in ("0", "1"):
                        pop = int(instruction[i][1::])
                    else:
                        print(f"Error at line {pc}: invalid value after a P")
                        exit()
                else:
                    print(f"Error at line {pc}: invalid value after a P")
                    exit()
            elif instruction[i].startswith("V"):
                if instruction[i][1] in ("0", "1"):
                    value = int(instruction[i][1::])
                else:
                    print(f"Error at line {pc}: invalid value after a V")

                    exit()
            elif instruction[i].startswith("F"):
                if instruction[i][1::] in ("0", "1", "2", "3"):
                    flag = int(instruction[i][1::])
                else:
                    print(f"Error at line {pc}: invalid value after a F")
                    exit()
            elif instruction[i].startswith("$"):
                if instruction[i][1] == "[":
                    if instruction[i][1::] in labels:
                        label = instruction[i][1::]
                    else:
                        print(f"Error at line {pc}: label does not exist")
                        exit()
                elif instruction[i][1::].isdigit() or instruction[i][1] == "-" and instruction[i][2::].isdigit():
                    if int(instruction[i][1::]) < 256 or int(instruction[i][1::]) > -257:
                        if instruction[i][1] == "-":
                            immediate = 255 - int(instruction[i][2::]) + 1
                        else:
                            immediate = int(instruction[i][1::])
                    else:
                        print(f"Error at line {pc}: immediate cannot be bigger than 255 or smaller than -256")
                        print(int(instruction[i][1::]))
                        exit()
                else:
                    print(f"Error at line {pc}: invalid value after a $")
                    exit()
            elif instruction[i][:2:] == "//":
                break
            else:
                print(f"Error at line {pc}: unrecognized opcode/operand")
                exit()

        if len(regs) > 0:
            regDest = regs[0]
        if len(regs) > 1:
            regA = regs[1]
        if len(regs) > 2:
            regB = regs[2]
        if len(regs) > 3:
            print(f"Error at line {pc}: too many registers")
            exit()

        '''
        print(instruction)
        print(f"Opcode: {opcode}  regDest: {regDest}  regA: {regA}  regB: {regB}   port: {port}  flag: {flag}  value: {value}  label: {label}  immediate: {immediate}  pop: {pop}")
        '''

        match opcode.lower():
            case "add":
                registers[regDest] = (registers[regA] + registers[regB]) % (2 ** cpu_bits)
                if registers[regA] + registers[regB] > 255:
                    flags[1] = True
                else:
                    flags[1] = False
            case "sub":
                registers[regDest] = (registers[regA] - registers[regB]) % 2 ** cpu_bits
                if registers[regA] > registers[regB]:
                    flags[1] = True
                else:
                    flags[1] = False
                if debug:
                    print(f"{registers[regA]} - {registers[regB]} = {registers[regA] - registers[regB]}")
            case "and":
                registers[regDest] = registers[regA] & registers[regB]
            case "or":
                registers[regDest] = registers[regA] | registers[regB]
            case "adc":
                if flags[1]:
                    registers[regDest] = (registers[regA] + registers[regB] + 1) % (2 ** cpu_bits)
                    if registers[regA] + registers[regB] + 1 > 255:
                        flags[1] = True
                    else:
                        flags[1] = False
                else:
                    registers[regDest] = (registers[regA] + registers[regB]) % (2 ** cpu_bits)
                    if registers[regA] + registers[regB] > 255:
                        flags[1] = True
                    else:
                        flags[1] = False
            case "rsh":
                registers[regDest] = registers[regA] >> 1
            case "adi":
                registers[regDest] = (registers[regDest] + immediate) % (2 ** cpu_bits)
                if registers[regDest] + immediate > 255:
                    flags[1] = True
                else:
                    flags[1] = False
            case "andi":
                registers[regDest] &= immediate
            case "xori":
                registers[regDest] ^= immediate
            case "ldi":
                registers[regDest] = immediate
            case "mst":
                ram[registers[7]] = registers[regDest]
            case "mld":
                registers[regDest] = ram[registers[7]]
            case "pst":
                portsO[port - 1] = registers[regDest]
                if file == "fibonacci":
                    print(portsO[0])
            case "pld":
                registers[regDest] = int(input(f"Input for port {port}\n"))  # portsI[port - 1]
            case "brc":
                immediate = labels[label]
                if flags[flag] == value:
                    pc = immediate
                else:
                    pc += 1
            case "jmp":
                try:
                    immediate = labels[label]
                except:
                    print(f"Error at line {pc}: syntax error on label")
                    exit()
                if pop == 0:
                    pc = immediate
                else:
                    pc = stack.pop(0)
            case "jal":
                immediate = labels[label]
                stack.insert(0, pc + 1)
                pc = immediate
            case "hlt":
                running = False
                print("Execution ended")
                exit()

        if debug:
            print(f"Cycles: {cycles}  PC: {pc}")

        if opcode.lower() not in ("brc", "jmp", "jal"):
            pc += 1

        cycles += 1

        if opcode.lower() in ["add", "sub", "and", "or", "adc", "adi", "andi", "xori"]:
            if registers[regDest] > 127:
                flags[0] = True
            else:
                flags[0] = False
            if registers[regDest] == 0:
                flags[2] = True
            else:
                flags[2] = False
            if registers[regDest] % 2 == 1:
                flags[3] = True
            else:
                flags[3] = False

        '''if cycles > 1_000_000:
            running = False'''

        if display:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    print("Execution ended")

        if not portsO[1] == old_port_1 and file == "bouncing ball":
            draw_grid()
            draw_pixel((portsO[0], portsO[1]))
            pygame.display.flip()

        if not portsO[0] == old_port_0 and file == "collatz":
            print(portsO[0])

        old_port_0 = portsO[0]
        old_port_1 = portsO[1]


file = "fibonacci"

emulate(r"C:\Users\zPippo\Desktop\Incel2's emulator\programs\{}.txt".format(file), False, False)

pygame.quit()
