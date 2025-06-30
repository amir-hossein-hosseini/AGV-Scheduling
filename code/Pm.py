# Function: Solving Pm|maintenance| by Cplex


def Pm (n,m,d,Time):
    import cplex
    import timeit
    import numpy as np


    c = cplex.Cplex()
    c.objective.set_sense(c.objective.sense.minimize)

    # Adding variables to model
    # X_{j,i}: if job j is assigned to AGV i
    for j in range(1, n + 1):
        for i in range(1, m + 1):
            varname = f"X_{j},{i}"
            c.variables.add(
                lb=[0],
                names=[varname],
                types=c.variables.type.binary,
                )

                

    # C_{i}: completion time (last job's deliovery time) of AGV i
    for i in range(1, m + 1):
        varname = f"C_{i}"
        c.variables.add(
            lb=[0], names=[varname], types=c.variables.type.integer
        )

    # C_Max
    c.variables.add(
        lb=[0], names=["C_Max"], types=c.variables.type.integer
    )

    # Adding objective function

    c.objective.set_linear("C_Max", 1)

    # Adding Constraints:
    # Set 1: all jobs need to be assigned to exactly one AGV:
    for j in range(1, n + 1):
        var = [None] * (m )
        coe = [None] * (m )
        h = 0
        for i in range(1, m + 1):
                var[h] = f"X_{j},{i}"
                coe[h] = 1.0
                h = h + 1
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["E"],
            rhs=[1.0],
        )
    

    # Set 2: Completion time:
    for i in range(1, m + 1):
        var = [None] * (n+1)
        coe = [None] * (n+1)
        h = 0
        for j in range(1, n + 1):
                var[h] = f"X_{j},{i}"
                coe[h] = d[ j - 1]
                h = h + 1
        var[h] = f"C_{i}"
        coe[h] = -1.0
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[0.0],
        )


    # Set 3: Makespan calculation:

    for i in range(1, m + 1):
        var = [None] * (2)
        coe = [None] * (2)
        h = 0
        var[h] = f"C_Max"
        coe[h] = -1.0
        h = h + 1
        var[h] = f"C_{i}"
        coe[h] = 1.0
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[0],
        )
   # c.write("AAAAAA.lp")


    start = timeit.default_timer()
    c.parameters.mip.display.set(0)
    c.parameters.timelimit.set(Time)
    c.solve()
    c.set_log_stream(None)
    stop = timeit.default_timer()
    Running_Time = stop - start
    LB=c.solution.MIP.get_best_objective()
    UB=c.solution.get_objective_value()
    Gap=c.solution.MIP.get_mip_relative_gap()

  #  print("Bin Packing Solution")
  #  print("LB=",LB)
  #  print("UB=",UB)
  #  print("Time=",time)


  #  X = np.zeros((n, m))
  #  for j in range(1, n+1):
  #      for i in range(1, m+1):
  #          if c.solution.get_values(f"X_{j},{i}") >0:
  #               X[j-1,i-1]=1 
  #  print(X)


    C=[None]*m
    for i in range(1, m+1):
        C[i-1]=int(c.solution.get_values(f"C_{i}"))
 #   print("Completion times=",C)
    

    Number_of_assigned_jobs=[0]*m
    for i in range(1, m+1):
        for j in range(1, n+1):
                if c.solution.get_values(f"X_{j},{i}") >0:
                    Number_of_assigned_jobs[i-1]=Number_of_assigned_jobs[i-1]+1
                    
#    print(Number_of_assigned_jobs)

    AJ = np.zeros((m,max(Number_of_assigned_jobs)))
    for i in range(1, m+1):
        l=0
        Assigned_jobs=[None]* Number_of_assigned_jobs[i-1]
        for j in range(1, n+1):
                if c.solution.get_values(f"X_{j},{i}") >0:
                    Assigned_jobs[l]=j
                    AJ[i-1,l]=j
                    l=l+1
            
    #    print("Assinged jobs to machine",f"{i}=", Assigned_jobs)  
#    print(AJ)
    return [LB, UB, AJ, Number_of_assigned_jobs,Gap,Running_Time]



        
#n=12
#m=2
#d=[11, 6, 16,13,15,32,8,8,9,7,60,60]
#T=900
#Pm (n,m,d,T)



