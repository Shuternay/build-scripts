# contest: Thumbtack Final 13-14
# problem: Game
#
# Correct solution, python3
# 100 / 100

__author__ = 'ksg'

T = int(input().split()[0])

for t in range(T):
    d = int(input().split()[0])

    sizes = input().split()[1:]

    ans = "First"

    for cur in sizes:
        ans = "Second" if int(cur) < d else ans

    print(ans)
