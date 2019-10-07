import numpy as np
from scipy.special import binom


# Equation
def memory_retrieval(input_pattern, patterns, control_bits_n, nvalue):
    i = input_pattern
    pi = np.pi
    b = control_bits_n
    p = len(patterns)
    n = len(input_pattern)
    
    #Probabilities array
    p_array = []
    
    #For each number of 1 bits
    for l in range(b+1):
        amp = binom(b, l) * (1/p)
        sum_value = 0
        for k in range(p):
            dh = hamming_distance(i, patterns[k])
            v = (pi/(2*n * nvalue))*dh
            
            sum_value += (np.cos(v)**(2*b-2*l)) * (np.sin(v)**(2*l))
            
        p_array.append(amp * sum_value)
    
    return p_array


# Equation 1
def memory_retrieval_1cbit(input_pattern, patterns):
    i = input_pattern
    pi = np.pi
    p = len(patterns)
    n = len(input_pattern)
    
    amp = 1/p
    
    sum_value = 0
    for k in range(p):
        dh = hamming_distance(i, patterns[k])
        v = (pi/(2*n))*dh
        
        sum_value += np.cos(v)**2
    
    return amp * sum_value


# Computes the Hamming distance
def hamming_distance(u, v):
    diff_n = 0

    for value1, value2 in zip(u, v):
        if value1 != value2:
            diff_n += 1

    return diff_n
