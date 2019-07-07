#!/usr/bin/env python3

import sys
import subprocess
import math
import itertools
from subprocess import PIPE


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
    # TODO figure out what reprobench expects in this case
    if solution == "UNSAT":
        print("Sudoku has no solution!")
        return

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
                    if val in puzzle[row][col]:
                        cell_vars.append(cell_to_int(row, col, val, size))
                    else:
                        f.write("-" + str(cell_to_int(row, col, val, size)) + " 0\n")
                if len(cell_vars) > 10:
                    f.write(exactly_one_out_of_circuit(cell_vars))
                else:
                    f.write(exactly_one_out_of_primitive(cell_vars))

        # row restrictions
        for col in range(size):
            for val in range(1, size+1):
                row_vars = []
                for row in range(size):
                    if val in puzzle[row][col]:
                        row_vars.append(cell_to_int(row, col, val, size))
                if len(row_vars) > 10:
                    f.write(exactly_one_out_of_circuit(row_vars))
                elif len(row_vars) > 1:
                    f.write(exactly_one_out_of_primitive(row_vars))

        # col restrictions
        for row in range(size):
            for val in range(1, size+1):
                col_vars = []
                for col in range(size):
                    if val in puzzle[row][col]:
                        col_vars.append(cell_to_int(row, col, val, size))
                if len(col_vars) > 10:
                    f.write(exactly_one_out_of_circuit(col_vars))
                elif len(col_vars) > 1:
                    f.write(exactly_one_out_of_primitive(col_vars))

        # subsudoku restrictions
        sub_size = round(math.sqrt(size))
        for val in range(1, size + 1):
            for subsudoku_row in range(sub_size):
                for subsudoku_col in range(sub_size):
                    subsudoku_vars = []
                    for row in range(subsudoku_row*sub_size, (subsudoku_row+1)*sub_size):
                        for col in range(subsudoku_col*sub_size, (subsudoku_col+1)*sub_size):
                            if val in puzzle[row][col]:
                                subsudoku_vars.append(cell_to_int(row, col, val, size))
                    if len(subsudoku_vars) > 10:
                        f.write(exactly_one_out_of_circuit(subsudoku_vars))
                    elif len(subsudoku_vars) > 1:
                        f.write(exactly_one_out_of_primitive(subsudoku_vars))


def exactly_one_out_of_circuit(list_of_vars):
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
    # first carry is (like all carries) false
    ret += "-" + str(carries[0]) + " 0\n"

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


def get_same_subsudoku(row_index, col_index, size):
    subsize = round(math.sqrt(size))
    """ Return all cells (r, c) which are in the same subsudoku as (row_index, col_index) """
    for r in range((row_index // subsize) * subsize, ((row_index // subsize) + 1) * subsize):
        for c in range((col_index // subsize) * subsize, ((col_index // subsize) + 1) * subsize):
            yield r, c


def preprocess(puzzle):
    size = len(puzzle)
    subsize = round(math.sqrt(size))

    for i, row in enumerate(puzzle):
        for j, cell in enumerate(row):
            if cell == 0:
                puzzle[i][j] = [i for i in range(1,size+1)]
            else:
                puzzle[i][j] = [cell]

    changes = True
    iterations = 0
    while changes and iterations < 10:
        changes = False
        iterations += 1
        numchanges = 0

        # Naked Single propagation: for a determined cell, remove its value from all cells in the same row/col/subsudoku
        for row_index, row in enumerate(puzzle):
            for col_index, cell in enumerate(row):
                if len(cell) == 1:
                    val = cell[0]
                    for r in range(size):
                        if r != row_index and val in puzzle[r][col_index]:
                            puzzle[r][col_index].remove(val)
                            changes = True
                            numchanges += 1
                    for c in range(size):
                        if c != col_index and val in puzzle[row_index][c]:
                            puzzle[row_index][c].remove(val)
                            changes = True
                            numchanges += 1
                    for r, c in get_same_subsudoku(row_index, col_index, size):
                        if (r != row_index or c != col_index) and val in puzzle[r][c]:
                            puzzle[r][c].remove(val)
                            changes = True
                            numchanges += 1

        # included in intersection removal
        # Hidden Single: if there's a row/col/subsudoku where a value is only possible in only one spot, fill that spot
        # for val in range(1, size+2):
        #
        #     # iterating over rows
        #     for row_index in range(size):
        #         row = puzzle[row_index]
        #         # if value already determined in row, do nothing
        #         if [val] in row:
        #             continue
        #         # Python magic
        #         riter = iter(row)
        #         if any(val in cell for cell in riter) and not any(val in cell for cell in riter):
        #             for col_index in range(size):
        #                 if val in row[col_index]:
        #                     puzzle[row_index][col_index] = [val]
        #
        #     # iterating over columns
        #     for col_index in range(size):
        #         col = [row[col_index] for row in puzzle]
        #         # if value already determined in column, do nothing
        #         if [val] in col:
        #             continue
        #         # Python magic
        #         citer = iter(col)
        #         if any(val in cell for cell in citer) and not any(val in cell for cell in citer):
        #             for row_index in range(size):
        #                 if val in col[row_index]:
        #                     puzzle[row_index][col_index] = [val]
        #
        #     for subsudoku_row in range(subsize):
        #         for subsudoku_col in range(subsize):
        #             subsudoku = [puzzle[r][c] for r, c in
        #                          get_same_subsudoku(subsudoku_row*subsize, subsudoku_col*subsize, size)]
        #             # if value already determined in subsudoku, do nothing
        #             if [val] in subsudoku:
        #                 continue
        #             siter = iter(subsudoku)
        #             if any(val in cell for cell in siter) and not any(val in cell for cell in siter):
        #                 for r in range(subsize):
        #                     for c in range(subsize):
        #                         row_index = subsudoku_row*subsize + r
        #                         col_index = subsudoku_col*subsize + c
        #                         if val in puzzle[row_index][col_index]:
        #                             puzzle[row_index][col_index] = [val]

        # intersection removal
        for val in range(1, size+1):

            # when all occurrences of val in row are in same subsudoku, remove all other val from subsudoku
            for row_index in range(size):
                occurrences = [col for col in range(size) if val in puzzle[row_index][col]]
                if len(occurrences) < 1:
                    continue
                candidate_subsudoku_col = occurrences[0] // subsize
                # handle hidden single
                if len(occurrences) == 1:
                    puzzle[row_index][occurrences[0]] = [val]
                if all(candidate_subsudoku_col == col // subsize for col in occurrences):
                    for r, c in get_same_subsudoku(row_index, candidate_subsudoku_col*subsize, size):
                        if r != row_index and val in puzzle[r][c]:
                            puzzle[r][c].remove(val)
                            changes = True
                            numchanges += 1

            # when all occurrences of val in col are in same subsudoku, remove all other val from subsudoku
            for col_index in range(size):
                occurrences = [row for row in range(size) if val in puzzle[row][col_index]]
                if len(occurrences) < 1:
                    continue
                candidate_subsudoku_row = occurrences[0] // subsize
                # handle hidden single
                if len(occurrences) == 1:
                    puzzle[occurrences[0]][col_index] = [val]
                if all(candidate_subsudoku_row == row // subsize for row in occurrences):
                    for r, c in get_same_subsudoku(candidate_subsudoku_row*subsize, col_index, size):
                        if c != col_index and val in puzzle[r][c]:
                            puzzle[r][c].remove(val)
                            changes = True
                            numchanges += 1

            for subsudoku_row in range(subsize):
                for subsudoku_col in range(subsize):
                    occurrences = [(row, col) for row, col
                                   in get_same_subsudoku(subsudoku_row*subsize, subsudoku_col*subsize, size)
                                   if val in puzzle[row][col]]
                    if len(occurrences) < 1:
                        continue
                    candidate_row = occurrences[0][0]
                    candidate_col = occurrences[0][1]
                    # handle hidden single
                    if len(occurrences) == 1:
                        puzzle[candidate_row][candidate_col] = [val]
                    # when all occurrences of val in box are in the same row, remove all other val from row
                    if all(candidate_row == r for r, _ in occurrences):
                        for c_del in range(size):
                            # only delete from cell in row if column yields different subsudoku
                            if c_del // subsize != candidate_col // subsize and val in puzzle[candidate_row][c_del]:
                                puzzle[candidate_row][c_del].remove(val)
                                changes = True
                                numchanges += 1
                    # when all occurrences of val in box are in the same col, remove all other val from col
                    if all(candidate_col == c for _, c in occurrences):
                        for r_del in range(size):
                            # only delete from cell in column if row yields different subsudoku
                            if r_del // subsize != candidate_row // subsize and val in puzzle[r_del][candidate_col]:
                                puzzle[r_del][candidate_col].remove(val)
                                changes = True
                                numchanges += 1

        # Classic X wing
        for val in range(1, size+1):
            # with locked rows
            locked_pairs = {}
            for row_index in range(size):
                occurrences = [col for col in range(size) if val in puzzle[row_index][col]]
                if len(occurrences) == 2:
                    if (occurrences[0], occurrences[1]) in locked_pairs.values():
                        for r in locked_pairs:
                            if locked_pairs[r] == (occurrences[0], occurrences[1]):
                                other_row = r
                                break
                        for r in range(size):
                            if r != row_index and r != other_row:
                                if val in puzzle[r][occurrences[0]]:
                                    puzzle[r][occurrences[0]].remove(val)
                                    changes = True
                                    numchanges += 1
                                if val in puzzle[r][occurrences[1]]:
                                    puzzle[r][occurrences[1]].remove(val)
                                    changes = True
                                    numchanges += 1
                    locked_pairs[row_index] = (occurrences[0], occurrences[1])

            # with locked cols
            locked_pairs = {}
            for col_index in range(size):
                occurrences = [row for row in range(size) if val in puzzle[row][col_index]]
                if len(occurrences) == 2:
                    if (occurrences[0], occurrences[1]) in locked_pairs.values():
                        for c in locked_pairs:
                            if locked_pairs[c] == (occurrences[0], occurrences[1]):
                                other_col = c
                                break
                        for c in range(size):
                            if c != col_index and c != other_col:
                                if val in puzzle[occurrences[0]][c]:
                                    puzzle[occurrences[0]][c].remove(val)
                                    changes = True
                                    numchanges += 1
                                if val in puzzle[occurrences[1]][c]:
                                    puzzle[occurrences[1]][c].remove(val)
                                    changes = True
                                    numchanges += 1
                    locked_pairs[col_index] = (occurrences[0], occurrences[1])

        print(numchanges)
        
        if [] in [cell for row in puzzle for cell in row]:
            return "UNSAT"


def solve(puzzle, solver, input_path):
    size = len(puzzle)
    global next_unused_variable
    next_unused_variable = size**3 + 1

    res = preprocess(puzzle)

    print("Finished preprocessing")

    if res == "UNSAT":
        return res

    # debug printing
    #for line in puzzle:
    #    l = ""
    #    for cells in line:
    #        l += str(cells) + "   "*(5-len(cells))
    #    print(l)

    cnf_path = input_path[:-3] + "cnf"
    create_cnf(puzzle, cnf_path)

    print("Finished writing CNF file")

    if solver != "clasp":
        print("Only supporting clasp atm")
        return

    clasp_out = subprocess.run(["clasp", "1", cnf_path], capture_output=True)
    clasp_out = clasp_out.stdout.decode()

    print("Finished SAT solving")

    # process clasp output
    if "UNSATISFIABLE" in clasp_out:
        return "UNSAT"
    for line in clasp_out.splitlines():
        if line[0] == "v":
            variables = line[2:].split(" ")
            # if variables out of sudoku range (i.e., auxillary variables), stop decoding solution
            if abs(int(variables[0])) > size**3:
                break
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
