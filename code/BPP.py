# Function: Solving Bin packing problem by Cplex

def BPP (n,e,T,BC=10):
    import cplex
    import timeit
    import numpy as np

  
    c = cplex.Cplex()
    c.objective.set_sense(c.objective.sense.minimize)

    # Adding variables to model
    # X_{j,i}: if job j is assigned to bin of  i
    for j in range(1, n + 1):
        for i in range(1, n + 1):
                varname = f"X_{j},{i}"
                c.variables.add(
                    lb=[0],
                    names=[varname],
                    types=c.variables.type.binary,
                )

    # Y_{i,k}: if kth bin of AGV i is used
    for i in range(1, n + 1):
            varname = f"Y_{i}"
            c.variables.add(
                lb=[0], names=[varname], types=c.variables.type.binary
            )

    # Number of used bins
    c.variables.add(
        lb=[0], names=["Bins"], types=c.variables.type.integer
    )

    # Adding objective function

    c.objective.set_linear("Bins", 1)

    # Adding Constraints:
    # Set 1: all jobs need to be assigned:
    for j in range(1, n + 1):
        var = [None] * (n)
        coe = [None] * (n)
        h = 0
        for i in range(1, n+ 1):
                var[h] = f"X_{j},{i}"
                coe[h] = 1.0
                h = h + 1
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["E"],
            rhs=[1.0],
        )


    # Set 2: Bin capacity must be respected:
    for i in range(1, n + 1):
        var = [None] * (n+1)
        coe = [None] * (n+1)
        h = 0
        for j in range(1, n + 1):
            var[h] = f"X_{j},{i}"
            coe[h] = e[j-1]
            h = h + 1
        var[h] = f"Y_{i}"
        coe[h] = -BC     

        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[0.0],
        )

    # Set 3: Symmytry breaking:
    for i in range(2, n + 1):
        var = [None] * 2
        coe = [None] * 2
        var[0]=f"Y_{i}"
        coe[0]=1
        var[1]=f"Y_{i-1}"
        coe[1]=-1
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[0.0],
        )
        


    # Set 4: Comuting number of bins:

    var = [None] * (n+1)
    coe = [None] * (n+1)
    h = 0
    var[h] = f"Bins"
    coe[h] = 1.0
    h = h + 1
    for i in range(1, n+1):
        var[h] = f"Y_{i}"
        coe[h] = -1.0
        h=h+1
    c.linear_constraints.add(
        lin_expr=[cplex.SparsePair(ind=var, val=coe)],
        senses=["E"],
        rhs=[0],
    )


    # Solve and output the problem:

    start = timeit.default_timer()
    c.parameters.timelimit.set(T)
    c.parameters.mip.display.set(0)
    c.solve()
    c.set_log_stream(None)
    c.set_results_stream(None)
    stop = timeit.default_timer()
    Running_Time = stop - start

#    print("Bin Packing Solution")
#    print("LB=",c.solution.MIP.get_best_objective())
#    print("UB=",c.solution.get_objective_value())
#    print("Time=",time)

    LB=c.solution.MIP.get_best_objective()
    UB=c.solution.get_objective_value()
    Gap= Gap=(UB-LB)/LB

    X = [None]*n
    for j in range(1, n+1):
        for i in range(1, n+1):
            if c.solution.get_values(f"X_{j},{i}") >0:
                X[j-1]=i

 #   print("Bin of each item=",X)

    return [LB, UB, X, Gap, Running_Time]


#e=[1,1,2,2,5,8]
#n=6
#T=60
#BPP(n,e,T)