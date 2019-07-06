#!/usr/bin/env python3

import sys
import subprocess
import math
import itertools


MAX_NUMBER = 0  # typically 9, 16, 25,...
DIMENSION = 0   # typically 3,  4,  5,...



# read input file
def read_input(input_path):
    with open(input_path, 'r') as input_file:
        global MAX_NUMBER
        global DIMENSION
        global first_lines
        first_lines = []
        line = input_file.readline()    # do not need this line
        first_lines.append(line)
        line = input_file.readline()    # do not need this line
        first_lines.append(line)
        line = input_file.readline()    # do not need this line
        first_lines.append(line)

        line = input_file.readline()
        first_lines.append(line)
        _, size = line.split(': ') 
        MAX_NUMBER,_ = size.split('x')  # typically 9, 16, 25,...
        MAX_NUMBER = int(MAX_NUMBER)
        DIMENSION = int(math.sqrt(MAX_NUMBER))
        puzzle = MAX_NUMBER*[0] # empty sudoku puzzle
        for i in range(MAX_NUMBER):
            puzzle[i] = MAX_NUMBER*[0] # empty sudoku puzzle
        i = 0 # counts the rows
        for line in input_file:
            if line[0] != '+' and i < MAX_NUMBER:
                #build list of all numbers in the ith row
                numbers = line.split('|')               # select all numbers
                numbers = numbers[1: len(numbers) -1]   # delete first and last element   
                s = ""
                for j in range(DIMENSION):
                   s = s + numbers[j][0: len(numbers[j])]
                n = s.split(' ')

                numbers = []
                for j in range(len(n)):
                    if n[j] != '':
                        numbers.append(n[j])

                if MAX_NUMBER != len(numbers):
                    print("ERROR: something went horribly wrong :(")
                # put the numbers into the puzzle
                for j in range(MAX_NUMBER):
                    if numbers[j].isdigit():    # check, if there is an entry, or an placeholder
                        puzzle[i][j] = int(numbers[j])
                i += 1
        return puzzle

# prints the solved puzzle
def print_output(solution):
    for i in range(len(first_lines)):
        print(first_lines[i], end = '')

    symbol_length = len(str(MAX_NUMBER)) # each numer should have this length
    for i in range(DIMENSION):
        print(DIMENSION*("+"+(DIMENSION*(symbol_length+1)+1)*"-")+"+")
        for l in range(DIMENSION):
            for j in range(DIMENSION):
                print("| ", end = '')
                for k in range(DIMENSION):
                    number = solution[i*DIMENSION+l][j*DIMENSION+k]
                    number = max(number,2)
                    empty = (symbol_length-len(str(number)))*" "
                    print(empty + str(solution[i*DIMENSION+l][j*DIMENSION+k]), end = ' ')
            print("|")

    print(DIMENSION*("+"+(DIMENSION*(symbol_length+1)+1)*"-")+"+")


def create_cnf(puzzle, path_to_cnf):
    size = len(puzzle)

    with open(path_to_cnf, 'w') as f:

        f.write("p cnf " + str(size**3 + 4*size**2*2*(size-1)) + " 12345\n")

        # cell restrictions
        for row in range(size):
            for col in range(size):
                cell_vars = []
                for val in range(1, size+1):
                    cell_vars.append(cell_to_int(row, col, val, size))
                f.write(exactly_one_out_of(cell_vars))

        # row restrictions
        for col in range(size):
            for val in range(1, size+1):
                row_vars = []
                for row in range(size):
                    row_vars.append(cell_to_int(row, col, val, size))
                f.write(exactly_one_out_of(row_vars))

        # col restrictions
        for row in range(size):
            for val in range(1, size+1):
                col_vars = []
                for col in range(size):
                    col_vars.append(cell_to_int(row, col, val, size))
                f.write(exactly_one_out_of(col_vars))

        # subsudoku restrictions
        sub_size = round(math.sqrt(size))
        for val in range(1, size + 1):
            for subsudoku_row in range(sub_size):
                for subsudoku_col in range(sub_size):
                    subsudoku_vars = []
                    for row in range(subsudoku_row*sub_size, (subsudoku_row+1)*sub_size):
                        for col in range(subsudoku_col*sub_size, (subsudoku_col+1)*sub_size):
                            subsudoku_vars.append(cell_to_int(row, col, val, size))
                    f.write(exactly_one_out_of(subsudoku_vars))

        # given variables
        for row_index, row in enumerate(puzzle):
            for col_index, cell in enumerate(row):
                if cell != 0:
                    f.write(str(cell_to_int(row_index, col_index, cell, size)) + " 0\n")


def exactly_one_out_of(list_of_vars):
    """
    CNF for 1-out-of-n constraints using half adder circuit logic
    """
    global next_unused_variable
    sums = [next_unused_variable+i for i in range(len(list_of_vars)-1)]
    next_unused_variable += len(list_of_vars) - 1
    carries = [next_unused_variable+i for i in range(len(list_of_vars)-1)]
    next_unused_variable += len(list_of_vars) - 1

    ret = ""

    # first carry is v0 AND v1
    ret += str(list_of_vars[0]) + " -" + str(carries[0]) + " 0\n"
    ret += str(list_of_vars[1]) + " -" + str(carries[0]) + " 0\n"
    ret += "-" + str(list_of_vars[0]) + " -" + str(list_of_vars[1]) + " " + str(carries[0]) + " 0\n"

    # first sum is v0 XOR v1
    ret += str(list_of_vars[0]) + " " + str(list_of_vars[1]) + " -" + str(sums[0]) + " 0\n"
    ret += "-" + str(list_of_vars[0]) + " -" + str(list_of_vars[1]) + " -" + str(sums[0]) + " 0\n"
    ret += "-" + str(list_of_vars[0]) + " " + str(list_of_vars[1]) + " " + str(sums[0]) + " 0\n"
    ret += str(list_of_vars[0]) + " -" + str(list_of_vars[1]) + " " + str(sums[0]) + " 0\n"

    for i in range(1,len(list_of_vars)-1):
        # carry is previous sum AND next variable
        # CNF (~cn | vn+1) & (~cn | sn-1) & (~vn+1 | ~sn-1 | cn)
        ret += str(list_of_vars[i+1]) + " -" + str(carries[i]) + " 0\n"
        ret += str(sums[i-1]) + " -" + str(carries[i]) + " 0\n"
        ret += "-" + str(list_of_vars[i+1]) + " -" + str(sums[i-1]) + " " + str(carries[i]) + " 0\n"

        # sum is previous sum XOR next variable
        # CNF (~sn | vn+1 | sn-1) & (~sn | ~sn-1 | ~vn+1) & (~vn+1 | sn-1 | sn) & (~sn-1 | vn+1 | sn)
        ret += "-" + str(sums[i]) + " " + str(list_of_vars[i+1]) + " " + str(sums[i-1]) + " 0\n"
        ret += "-" + str(sums[i]) + " -" + str(list_of_vars[i+1]) + " -" + str(sums[i-1]) + " 0\n"
        ret += "-" + str(list_of_vars[i+1]) + " " + str(sums[i]) + " " + str(sums[i-1]) + " 0\n"
        ret += str(list_of_vars[i+1]) + " -" + str(sums[i-1]) + " " + str(sums[i]) + " 0\n"

        # all carries are false
        ret += "-" + str(carries[i]) + " 0\n"

    # last sum is true
    ret += str(sums[-1]) + " 0\n"

    return ret


def exactly_one_out_of_primitive(list_of_vars):
    """
    Return a CNF that ensures exactly one out of a given list of variables is true for all satisfying assignments
    """
    ret = ""
    # at least one
    ret += " ".join(str(i) for i in list_of_vars) + " 0\n"
    # no two different variables
    for pair in itertools.combinations(list_of_vars, 2):
        ret += " ".join("-"+str(i) for i in pair) + " 0\n"

    return ret


def cell_to_int(row, col, val, size):
    """
    Return the integer that is the propositional variable representing
    val being present int cell (row, col) in a sudoku of given size
    """
    # note val ranges from 1 to size, so 0 is impossible
    return row * size**2 + col * size + val


def int_to_cell(prop_var, size):
    """
    Return the row, column and value of a cell represented
    by a propositional variable in a sudoku of given size
    """
    prop_var -= 1
    row = prop_var // size**2
    col = (prop_var % size**2) // size
    val = prop_var % size
    return row, col, val+1


def solve(puzzle, solver, input_path):
    size = len(puzzle)
    global next_unused_variable
    next_unused_variable = size**3 + 1

    cnf_path = input_path[:-3] + "cnf"
    create_cnf(puzzle, cnf_path)

    print("Finished writing CNF file")

    if solver != "clasp":
        print("Only supporting clasp atm")
        return

    clasp_out = subprocess.run(["clasp", "1", cnf_path], capture_output=True)
    # remove Windows-specific \r
    clasp_out = str(clasp_out.stdout).replace("\\r", "")

    # process clasp output
    for line in str(clasp_out).split("\\n"):
        if line[0] == "v":
            variables = line[2:].split(" ")
            for v in variables:
                prop_var = int(v)
                if size**3 >= prop_var > 0:
                    row, col, cell = int_to_cell(prop_var, size)
                    puzzle[row][col] = cell

    return puzzle


solver = sys.argv[1]
input_path = sys.argv[2]

puzzle = read_input(input_path)
solution = solve(puzzle, solver, input_path)
print_output(solution)
