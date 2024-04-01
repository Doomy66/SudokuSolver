from dataclasses import dataclass, field
from copy import deepcopy
from time import perf_counter
from collections import Counter
from typing import ClassVar


starttime = 0


@dataclass
class Point:
    row: int
    col: int
    value: int = 0
    failed: set = field(default_factory=set[int])
    _available: set = field(default_factory=set[int])
    source: str = ' '

    @property
    def bigrow(self) -> int:
        """Larger 3x3 grid"""
        return int(self.row/3)

    @property
    def bigcol(self) -> int:
        """Larger 3x3 grid"""
        return int(self.col/3)


@dataclass
class Sudoku:
    startpos: str
    name: str = '<No Name>'
    points: list = field(default_factory=list[Point])
    # Are classvars instead of Globals for smartness. Need to reset them if you are to run multiple solutions in 1 run
    thinks: ClassVar[int] = 0
    guesses: ClassVar[int] = 0
    deductions: ClassVar[int] = 0
    fails: ClassVar[int] = 0
    maxlevel: ClassVar[int] = 0

    def __post_init__(self):
        # Fill with 0
        self.points = list(Point(int(_/9), _ % 9) for _ in range(9*9))

        point: Point
        if self.startpos:
            # Apply Start Posistion
            for point in self.points:
                c: str = f"{self.startpos:81}"[point.col+9*point.row]
                point.value = int(c) if c in "123456789" else 0
        else:
            # A default position if you have forgotten to pass one
            self.points[4+(9*4)].value = 1

    def display(self, source: bool = False) -> None:
        """ Outputs the position in human readable format\n
        source=True will show characters indicating where each value comes from\n
             = Think, * Deduce, a 1st Guess, b 2nd Guess etc """
        point: Point
        if self.name:
            print(f"{self.name} - {Sudoku.thinks+Sudoku.deductions+Sudoku.guesses}")
        for point in self.points:
            print(
                f" {point.value if point.value else '.'}{point.source if source else ' '}{'|' if point.col==2 or point.col == 5 else ''}", end='')
            if point.col == 8:
                print('')
                if point.row == 2 or point.row == 5:
                    print("---------+---------+---------")
        print('')

    def onrow(self, point: Point) -> set[int]:
        """Set of all values on the row of the point"""
        return set(_.value for _ in self.points if (_.value != 0 and _.row == point.row))

    def oncol(self, point: Point) -> set[int]:
        """Set of all values on the column of the point"""
        return set(_.value for _ in self.points if (_.value != 0 and _.col == point.col))

    def in3x3(self, point: Point) -> set[int]:
        """Set of all values in the same 3x3 of the point"""
        return set(_.value for _ in self.points if (_.value != 0 and _.bigrow == point.bigrow and _.bigcol == point.bigcol))

    def used(self, point: Point) -> set[int]:
        """Set of values that are not available"""
        return self.oncol(point) | self.onrow(point) | self.in3x3(point) | point.failed

    def available(self, point: Point) -> set[int]:
        """Set of available values.\n
        Value is Cached for speed. Need to run clearcache if state is altered"""
        if point.value == 0 and not point._available:
            point._available = {1, 2, 3, 4, 5, 6, 7, 8, 9} - self.used(point)
        return point._available

    def deduce(self, point: Point) -> set[int]:
        """ Deduce if this point has only 1 possible value """
        deducerow = set()
        deducecol = set()
        p: Point
        for p in self.points:
            if point != p and p.value == 0:
                if point.row == p.row:
                    deducerow |= self.available(p)
                elif point.col == p.col:
                    deducecol |= self.available(p)

        # if (len(ans := self.available(point)-deducerow)) == 1 and ans == self.available(point)-deducecol:
        if (len(ans := self.available(point)-deducerow)) == 1 or (len(ans := self.available(point)-deducecol)) == 1:
            return ans
        else:
            return set()

    def deduced(self) -> list[set[Point]]:
        ## List of points that can be deduced to a single value using the more advance method ##
        ans = list(p for p in self.points if p.value == 0 and len(
            self.available(p)) > 1 and self.deduce(p))
        return ans

    def todo(self) -> list[set[Point]]:
        """List of all Points with no value sorted by number of available values"""
        # NB Its a shallow copy so changes are reflected in self.grid
        ans = (p for p in self.points if p.value == 0)
        return sorted(ans, key=lambda p: len(self.available(p)))

    def tokenize(self, source: bool = False) -> str:
        """ Returns the state as a single string """
        if source:
            return ''.join(p.source for p in self.points)
        else:
            return ''.join('.' if p.value == 0 else str(p.value) for p in self.points)

    def clearcache(self) -> None:
        """ Clear the cache so available is recalculated """
        p: Point
        for p in self.points:
            p._available = set()

    def setpoint(self, point: Point, value: int, source: str = ' '):
        """ Set a point and clear cache"""
        point.value = value
        point.source = source
        self.clearcache()

    def failed(self, point: Point, value: int):
        """ Record a failure """
        Sudoku.fails += 1
        point.failed.add(value)
        self.clearcache()


def solve(s: Sudoku, level: int, deduce: bool = True):
    """ Solves a Sukdoku and displays the result.\nIf it has to guess, it will recurse """
    global starttime
    todo: Point
    if starttime == 0:
        starttime = perf_counter()
    Sudoku.maxlevel = max(Sudoku.maxlevel, level)

    # Known values
    while s.todo() and (len(s.available(s.todo()[0])) == 1 or (deduce and s.deduced())):
        if len(s.available(s.todo()[0])) == 1:
            todo = s.todo()[0]
            available = s.available(todo)
            s.setpoint(todo, next(iter(available)), '=')
            Sudoku.thinks += 1

        else:
            # We can deduce a/some points
            todo = s.deduced()[0]
            available = s.deduce(todo)
            s.setpoint(todo, next(iter(available)), '*')
            Sudoku.deductions += 1

    # Going to have to guess
    while s.todo():
        todo = s.todo()[0]   # Pick the best point to try
        # Check there is a value left to try
        if available := s.available(todo):
            use = next(iter(available))  # Value to try
            nextlevel = deepcopy(s)  # Make a copy of the current state
            nexttodo: Point = nextlevel.todo()[0]
            nextlevel.setpoint(nexttodo, use, 'abcedfghijk'[
                               len(nexttodo.failed)])
            Sudoku.guesses += 1
            # print('.' * level)
            # nextlevel.display()
            # Recurse to solve remaining points
            if solve(nextlevel, level+1, deduce):
                return True  # We have a Solution !
            else:
                # The guess does not lead to a solution, try another on this level
                s.failed(todo, use)
        else:
            # ANY point with no possible values means not a valid solution
            return False

    # We only get here when all points have a value
    s.display()
    print(
        f"Solved {s.name} with {Sudoku.thinks} thoughts, {Sudoku.deductions} deductions, {Sudoku.guesses} guesses, {Sudoku.fails} fails, {Sudoku.maxlevel} Max Level. {int(perf_counter()-starttime)}s")
    # print(s.tokenize())
    # print(s.tokenize(True))
    print(', '.join(f"({k}){v}" for k, v in Counter(s.tokenize(True)).items()))
    return True


if __name__ == '__main__':
    s = Sudoku('', 'Simple')  # A Default
    # Set Start Position
    # Example Puzzles
    # # Arto Inkala - ABC News
    # Solved Arto Inkala - ABC News with 438 thoughts, 581 deductions, 74 guesses, 68 fails, 10 Max Level. 8s
    # s = Sukoku(
    #     '8..........36......7..9.2...5...7.......457.....1...3...1....68..8...51..9....4..', 'Arto Inkala - ABC News')
    # AI Escargot
    # Solved AI Escargot with 157 thoughts, 113 deductions, 18 guesses, 10 fails, 8 Max Level. 1s : =23, *=8, ==42, a=4, b=4
    # s = Sukoku(
    #     '1....7.9..3..2...8..96..5....53..9...1..8...26....4...3......1..4......7..7...3..', 'AI Escargot')
    # # AI Killer Application
    # Solved AI Killer Application with 307 thoughts, 181 deductions, 34 guesses, 29 fails, 8 Max Level. 3s
    # s = Sukoku(
    #     '.......7..6..1...4..34..2..8....3.5...29..7...4..8...9.2..6...7...1..9..7....8.6.', 'AI Killer Application')
    # # AI Lucky Diamond
    # Solved AI Lucky Diamond with 521 thoughts, 422 deductions, 67 guesses, 61 fails, 10 Max Level. 6s
    # s = Sukoku(
    #     '1..5..4....9.3.....7...8..5..1....3.8..6..5...9...7..8..4.2..1.2..8..6.......1..2', 'AI Lucky Diamond')
    # # AI Wormhole
    # Solved AI Wormhole with 605 thoughts, 471 deductions, 68 guesses, 57 fails, 11 Max Level. 7s
    # s = Sukoku(
    #     '.8......1..7..4.2.6..3..7....2..9...1...6...8.3.4.......17..6...9...8..5.......4.', 'AI Wormhole')
    # # AI Labyrinth
    # Solved AI Labyrinth with 1073 thoughts, 1241 deductions, 161 guesses, 157 fails, 12 Max Level. 17s
    # s = Sukoku(
    #     '1..4..8...4..3...9..9..6.5..5.3..........16......7...2..4.1.9..7..8....4.2...4.8.', 'AI Labyrinth')
    # # AI Circles
    # Solved AI Circles with 1421 thoughts, 829 deductions, 164 guesses, 156 fails, 11 Max Level. 14s
    # s = Sukoku(
    #     '..5..97...6.....2.1..8....6.1.7....4..7.6..3.6....32.......6.4..9..5.1..8..1....2', 'AI Circles')
    # # AI Squadron
    # Solved AI Squadron with 731 thoughts, 551 deductions, 74 guesses, 67 fails, 9 Max Level. 9s
    # s = Sukoku(
    #     '6.....2...9...1..5..8.3..4......2..15..6..9....7.9.....7...3..2...4..5....6.7..8.', 'AI Squadron')
    # # AI Honeypot
    # Solved AI Honeypot with 149 thoughts, 137 deductions, 20 guesses, 13 fails, 7 Max Level. 2s
    # s = Sukoku(
    #     '1......6....1....3..5..29....9..1...7...4..8..3.5....25..4....6..8.6..7..7...5...', 'AI Honeypot')
    # # AI Tweezers
    # Solved AI Tweezers with 613 thoughts, 506 deductions, 75 guesses, 70 fails, 9 Max Level. 7s
    # s = Sukoku(
    #     '....1...4.3.2.....6....8.9...7.6...59....5.8....8..4...4.9..1..7....2.4...5.3...7', 'AI Tweezers')
    # # AI Broken Brick
    # Solved AI Broken Brick with 460 thoughts, 383 deductions, 51 guesses, 46 fails, 9 Max Level. 6s
    # s = Sukoku(
    #     '4...6..7.......6...3...2..17....85...1.4......2.95..........7.5..91...3...3.4..8.', 'AI Broken Brick')
    # Reddit r11.9
    # Result 128465379374219856956837142765198423249673581813542967592386714487921635631754298
    # Solved Reddit r11.9 with 3685 thoughts, 2874 deductions, 532 guesses, 522 fails, 14 Max Level. 46s
    # s = Sudoku(
    #     '12.4..3..3...1..5...6...1..7...9.....4.6.3.....3..2...5...8.7....7.....5.......98', "Reddit r11.9")

    print('Solving...')
    s.display()
    solve(s, 0)
