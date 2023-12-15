import math
from polynom import Polynom


def sin_taylor(k):
    x = Polynom([0, 1])
    sum = Polynom([0])
    for i in range(k):
        a = [0,1,0,-1][i%4]
        sum += (x**i)*(a/math.factorial(i))
    return sum
def cos_taylor(k):
    x = Polynom([0, 1])
    sum = Polynom([0])
    for i in range(k):
        a = [1,0,-1,0][i%4]
        sum += (x**i)*(a/math.factorial(i))
    return sum