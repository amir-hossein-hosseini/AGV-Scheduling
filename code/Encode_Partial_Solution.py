# Generate a partial encode of a given set of jobs (only normal jobs) to CPLEX variable array. The output can be used just for constructing Combinatorial cuts.
def Encode_Partial_Solution(Array_of_jobs,n,b0,b1,b2,m,AGV):
    Variable_Array=[0]*((n+b0+b1+b2)*m+m+1)
    for j in Array_of_jobs:
        Variable_Array[(j-1)*m+AGV]=1    
    return Variable_Array
