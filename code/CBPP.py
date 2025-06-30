# Function: Solving the crdinality bin packing problem (CBPP) by Cplex

def CBPP (Set_of_Jobs,b,e,Time,Number_of_Thread,BC=10):
    import cplex
    import timeit
    import numpy as np

    n=len(Set_of_Jobs)
    c = cplex.Cplex()
    c.objective.set_sense(c.objective.sense.maximize)

    # Adding variables to model
    # X_{j,i}: if job j is assigned to bin i
    for j in range(1, n + 1):
        for i in range(1, b + 1):
                varname = f"X_{j},{i}"
                c.variables.add(
                    lb=[0],
                    obj=[1.0],
                    names=[varname],
                    types=c.variables.type.binary,
                )


    # Adding Constraints:
    # Set 1: Summation of assigned jobs must be less than capacity of each bin
    for i in range(1, b + 1):
        var = [None] * (n)
        coe = [None] * (n)
        h = 0
        for j in range(1, n+ 1):
                var[h] = f"X_{j},{i}"
                coe[h] = e[j-1]
                h = h + 1
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[BC],
        )


    # Set 2: Bin capacity must be respected:
    for j in range(1, n + 1):
        var = [None] * (b)
        coe = [None] * (b)
        h = 0
        for i in range(1, b + 1):
            var[h] = f"X_{j},{i}"
            coe[h] = 1.0
            h = h + 1 

        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[1.0],
        )
    # Solve and output the problem:

    start = timeit.default_timer()
    c.parameters.timelimit.set(Time)
    c.parameters.mip.display.set(0)
    c.parameters.threads.set(Number_of_Thread)
    c.solve()
    stop = timeit.default_timer()
    time = stop - start

    LB=c.solution.get_objective_value()
    UB=c.solution.MIP.get_best_objective()
    Gap=c.solution.MIP.get_mip_relative_gap()
    Solution_Status=c.solution.get_status()

    Number_of_Accepted_Items =0
    for j in range(1, n+1):
        for i in range(1, b+1):
            if c.solution.get_values(f"X_{j},{i}") >0.1:
                Number_of_Accepted_Items=Number_of_Accepted_Items+1


    Set_of_Accepted_Jobs = [None]*int(Number_of_Accepted_Items)
    Set_of_Rejected_Jobs = [None]*(n-int(Number_of_Accepted_Items))

    h=0
    k=0
    for j in range(1, n+1):
        l=0
        for i in range(1, b+1):
            if c.solution.get_values(f"X_{j},{i}") >0.1:
                Set_of_Accepted_Jobs[h]=f"X_{j},{i}"
              #  Set_of_Accepted_Jobs[h]=j
                Set_of_Accepted_Jobs[h]=Set_of_Jobs[j-1]
                h=h+1
                l=1
        if l==0:
          #  Set_of_Rejected_Jobs[k]=j
            Set_of_Rejected_Jobs[k]=Set_of_Jobs[j-1]
            k=k+1

#    print("Set of accepted jobs", Set_of_Accepted_Jobs)
#    print("Set of rejected jobs", Set_of_Rejected_Jobs)
#    print("Solution statues of CBPP",Solution_Status )
#    print("Number of accepted jobs", Number_of_Accepted_Items)
#    print("Capacitated Bin Packing Solution")
#    print("LB=",c.solution.MIP.get_best_objective())
#    print("UB=",c.solution.get_objective_value())
#    print("Time=",time)

    return [LB, UB, Gap, Number_of_Accepted_Items,Set_of_Accepted_Jobs,Set_of_Rejected_Jobs,Solution_Status]


#e=[6.8, 4.1, 3.6, 5.7, 4.2, 5.1, 5.4, 4.2, 8.2, 4.9, 4.0, 2.1, 5.0, 6.4, 5.9, 3.7, 8.2, 5.0, 4.9, 8.5, 6.3, 5.5, 7.1, 0.6, 3.8, 4.8, 3.8, 3.8, 7.2, 8.3, 7.1, 6.3, 2.2, 6.1, 3.9, 6.2, 1.0, 2.2, 4.3, 4.1, 5.0, 8.0, 9.3, 5.0, 5.9, 1.7, 6.9, 4.5, 5.7, 1.5, 6.6, 8.2, 4.1, 3.7, 6.5, 5.7, 7.1, 4.2, 6.5, 1.7, 7.4, 3.5, 6.3, 3.5, 7.2, 5.6, 4.0, 1.1, 4.8, 2.0, 5.8, 8.4, 7.5, 5.6, 1.9, 7.8, 3.2, 7.3, 2.9, 5.3, 6.0, 5.7]
#n=len(e)
#Time=300
#b=44
#[UB, Number_of_Accepted_Items,Set_of_Accepted_Jobs,Set_of_Rejected_Jobs,Solution_Status]=CBPP (n,b,e,Time,BC=10)
#print(UB)
#print(Number_of_Accepted_Items)
#print(Set_of_Accepted_Jobs)
#print(Set_of_Rejected_Jobs)
#print(Solution_Status)