
# Function: generating all the subset of a given set (starting from the smallest sebset and without the empty set) 
#as the function is an exponential function, the parameter l determines the length of the subesets, l = 5, means only subsebts with up to 5 members.

import itertools

def Generate_Subsets(s,l):
    subsets = []
    for r in range(1,l + 1):
  #  for r in range(1,len(s) + 1):
        subsets.extend(itertools.combinations(s, r))
    return subsets
