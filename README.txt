# SodukuSolver
It solves Soduku puzzles very very quickly.
There is lots of terminology in the Soduku world which I have no clue about.

Create a variable of type Soduku supplying the staring postion as a 91 char string (reading order) with . o or space to indicate an unknown number
Pass the variable to solve

a Think is a simple deduction looking at the values in the current row, column and 3x3 area and finding a single valie
a Deduce is a smarter deduction that looks at other 3x3. An avergage puzzler will probably not use this technique very often. It is controlled by a parameter of solve()
a Guess is when there are more than 1 possible answer for a point, it will pick one.
a Fail is when the current state will not provide a solution


