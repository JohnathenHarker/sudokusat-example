#!/usr/bin/env python3

import sys
import math


MAX_NUMBER = 0  # typically 9, 16, 25,...
DIMENSION = 0



# read input file
def read_input(input_path):
    with open(input_path, 'r') as input_file:
        global MAX_NUMBER
        global DIMENSION
        line = input_file.readline()            # do not need this line
        line = input_file.readline()
        _, number_of_tasks = line.split(': ')   # do not need this
        line = input_file.readline()
        _, task = line.split(': ')              # do not need this

        line = input_file.readline()
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
                   s = s + numbers[j][0: len(numbers[j])-1]
                s = s[1:]   # delete first symbol (blank)
                numbers = s.split(' ')

                if MAX_NUMBER != len(numbers):
                    print("ERROR: something went horribly wrong :(")
                # put the numbers into the puzzle
                for j in range(MAX_NUMBER):
                    if numbers[j].isdigit():    # check, if there is an entry, or an placeholder
                        puzzle[i][j] = int(numbers[j])
                i += 1
        return puzzle





solver = sys.argv[1]
input_path = sys.argv[2]

#print("input_path:", input_path)
#print("solver:", solver)
puzzle = read_input(input_path)
print(puzzle)