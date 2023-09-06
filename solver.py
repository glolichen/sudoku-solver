import copy
import math

LARGE_CELL_SIGHT = 0b000000000000000000000000000000000000000000000000000000000000111000000111000000111
VERTICAL_SIGHT =   0b000000001000000001000000001000000001000000001000000001000000001000000001000000001
HORIZONTAL_SIGHT = 0b000000000000000000000000000000000000000000000000000000000000000000000000111111111
FULL_BOARD = 0b111111111111111111111111111111111111111111111111111111111111111111111111111111111

VERTICAL = 0
HORIZONTAL = 1
LARGE_CELL = 2
ALL = 3

CONFIRMED = 0
POTENTIAL_LOCATION = 1

# ensures we cover every row, column and large cell in the least number of runs (just 9)

# 1, 0, 0,  0, 0, 0,  0, 0, 0,
# 0, 0, 0,  1, 0, 0,  0, 0, 0,
# 0, 0, 0,  0, 0, 0,  1, 0, 0,

# 0, 1, 0,  0, 0, 0,  0, 0, 0,
# 0, 0, 0,  0, 1, 0,  0, 0, 0,
# 0, 0, 0,  0, 0, 0,  0, 1, 0,

# 0, 0, 1,  0, 0, 0,  0, 0, 0,
# 0, 0, 0,  0, 0, 1,  0, 0, 0,
# 0, 0, 0,  0, 0, 0,  0, 0, 1

NEED_RUN_TEST = [0, 12, 24, 28, 40, 52, 56, 68, 80]

CELL_VISION = []
for i in range(9):
	for j in range(9):
		vertical = VERTICAL_SIGHT << (8 - j)
		horizontal = HORIZONTAL_SIGHT << (9 * (8 - i))

		left = (8 - j) // 3
		top = (8 - i) // 3
		large_cell = LARGE_CELL_SIGHT << (top * 27 + left * 3)

		all = vertical | horizontal | large_cell

		CELL_VISION.append([vertical, horizontal, large_cell, all])

class Puzzle:
	def __init__(self, numbers, candidates):
		self.numbers = numbers
		self.candidates = candidates

def query(bitboard: int, position: int) -> int:
	return (bitboard >> (80 - position)) & 1
def toggle(bitboard: int, position: int) -> int:
	return bitboard ^ (1 << (80 - position))
def set1(bitboard: int, position: int) -> int:
	return bitboard | (1 << (80 - position))
def clz(bitboard: int) -> int:
	return 81 - bitboard.bit_length()
def ctz(bitboard: int) -> int:
	return int(math.log2(bitboard & -bitboard))
def print_bitboard(bitboard: int) -> None:
	b = bin(bitboard).lstrip("0b")
	b = ("0" * (81 - len(b))) + b
	for i in range(9):
		for j in range(9):
			print(b[i * 9 + j], end="")
		print()

def print_puzzle(puzzle: Puzzle, format: bool) -> None:
	for i in range(9):
		for j in range(9):
			index = i * 9 + j
			numberFound = -1
			for k in range(0, 10):
				if query(puzzle.numbers[k][CONFIRMED], index) == 1:
					if numberFound != -1:
						raise Exception("error with puzzle representation")
					numberFound = k
			print(numberFound, end=("  " if j % 3 == 2 else " ") if format else "")
		print("\n" if i % 3 == 2 and format else "")

# numbers[x][0/CONFIRMED]  {x != 0} = cells occupied by x (where x = 0 is any number)
# numbers[x][1/POTENTIAL_LOCATIONS] {x != 0} = cells where x is currently valid
# numbers[x][0/CONFIRMED]  {x == 0} = empty cells
# numbers[x][1/POTENTIAL_LOCATIONS] {x == 0} = not used

puzzle = Puzzle(
	[[0, FULL_BOARD] for _ in range(10)],
	[([False] + [True] * 9) for _ in range(81)]
)

def has_mistake(puzzle: Puzzle) -> bool:
	for i in range(81):
		if query(puzzle.numbers[0][CONFIRMED], i) != 0:
			if True not in puzzle.candidates[i]:
				return True
		
		for j in range(1, 10):
			for k in range(3):
				confirmed = puzzle.numbers[j][CONFIRMED] & CELL_VISION[i][k]
				if confirmed.bit_count() > 1:
					return True
				
	return False

def eliminate_candidates(puzzle: Puzzle, number: int) -> tuple:
	result = puzzle.numbers[number][POTENTIAL_LOCATION]
	candidates = puzzle.candidates
	current_locations = puzzle.numbers[number][CONFIRMED]
	while current_locations != 0:
		last_bit = current_locations & -current_locations
		current_locations ^= last_bit
		last_bit = 80 - int(math.log2(last_bit))
		eliminated = CELL_VISION[last_bit][ALL]
		result &= (eliminated ^ FULL_BOARD)
		while eliminated != 0:
			eliminated_cell = eliminated & -eliminated
			eliminated ^= eliminated_cell
			eliminated_cell = 80 - int(math.log2(eliminated_cell))
			candidates[eliminated_cell][number] = False

	result &= puzzle.numbers[0][CONFIRMED]
	return (result, candidates)

def find_correct(puzzle: Puzzle, number: int) -> int:
	result = puzzle.numbers[number][CONFIRMED]
	potential = puzzle.numbers[number][POTENTIAL_LOCATION]
	for i in NEED_RUN_TEST:
		for j in range(3):
			valid = potential & CELL_VISION[i][j]
			if valid == 0:
				continue
			position = clz(valid)
			if position + ctz(valid) == 80:
				result = set1(result, position)
	return result

def find_sole_candidate(puzzle: Puzzle) -> int:
	empty = puzzle.numbers[0][0]
	while empty != 0:
		index = empty & -empty
		empty ^= index
		index = 80 - int(math.log2(index))

		number = 0
		for j in range(1, 10):
			if puzzle.candidates[index][j]:
				if number != 0:
					number = -1
					break
				number = j
		if number > 0:
			puzzle.numbers[0][0] = set1(puzzle.numbers[0][0], index)
			puzzle.numbers[number][CONFIRMED] = set1(puzzle.numbers[number][CONFIRMED], index)

	return puzzle.numbers

def calculate(puzzle: Puzzle) -> tuple:
	changeMade = False
	for i in range(1, 10):
		change = eliminate_candidates(puzzle, i)
		puzzle.numbers[i][1] = change[0]
		puzzle.candidates = change[1]

		numberBitboard = find_correct(puzzle, i)
		if puzzle.numbers[i][CONFIRMED] != numberBitboard:
			changeMade = True
		puzzle.numbers[i][CONFIRMED] = numberBitboard
		puzzle.numbers[0][CONFIRMED] &= (numberBitboard ^ FULL_BOARD)

		puzzle.numbers = find_sole_candidate(puzzle)

	return (puzzle, changeMade)

class Action:
	def __init__(self, square: int, number: int):
		self.square = square
		self.number = number

def bifurcate(puzzle: Puzzle, action: Action) -> Puzzle:
	if action != None:
		puzzle.numbers[action.number][0] = set1(puzzle.numbers[action.number][0], action.square)
		puzzle.numbers[0][0] = set1(puzzle.numbers[0][0], action.square)

		changeMade = True
		while changeMade:
			puzzle, changeMade = calculate(puzzle)

		if has_mistake(puzzle):
			return None
		elif puzzle.numbers[0][0] == 0:
			return puzzle

	lowestSquare = -1
	lowestSquareCandidates = [0] * 100
	for i in range(81):
		if query(puzzle.numbers[0][CONFIRMED], i) == 0:
			continue

		candidates = puzzle.candidates[i]
		validCandidates = []

		for j in range(1, len(candidates)):
			if candidates[j] == True:
				validCandidates.append(j)

		if len(validCandidates) < len(lowestSquareCandidates):
			lowestSquare = i
			lowestSquareCandidates = validCandidates.copy()


	for i in range(len(lowestSquareCandidates)):
		outcome = bifurcate(copy.deepcopy(puzzle), Action(lowestSquare, lowestSquareCandidates[i]))
		if outcome == None:
			continue
		else:
			return outcome
		
	return 50

for i in range(9):
	line = input()
	if len(line) != 9:
		raise Exception("invalid puzzle")
	for j in range(9):
		if '0' <= line[j] <= '9':
			num = ord(line[j]) - ord('0')
			puzzle.numbers[num][0] = set1(puzzle.numbers[num][CONFIRMED], i * 9 + j)
		else:
			raise Exception("invalid puzzle")
		
changeMade = True
while changeMade:
	puzzle, changeMade = calculate(puzzle)
	
if puzzle.numbers[0][0] == 0:
	print_puzzle(puzzle, True)
else:
	outcome = bifurcate(puzzle, None)
	print_puzzle(outcome, True)

"""
test input:
037080509
006000000
000100800
600030000
053400070
100000005
000002040
098010007
500000000
"""

"""
output:
4 3 7  2 8 6  5 1 9  
8 1 6  3 9 5  7 2 4  
9 2 5  1 4 7  8 6 3  

6 7 9  5 3 1  4 8 2  
2 5 3  4 6 8  9 7 1  
1 8 4  7 2 9  6 3 5  

7 6 1  9 5 2  3 4 8  
3 9 8  6 1 4  2 5 7  
5 4 2  8 7 3  1 9 6  
"""