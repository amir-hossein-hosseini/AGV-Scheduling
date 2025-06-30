# Function: Generate and solve the Cplex model of the subproblem from MILP2 by Cplex

def SP_Feasibility_Check (Num_of_Jobs,Num_of_B0,Num_of_B1,Num_of_B2,m,AGV,e,BC,MP_Values,Time,Number_of_Thread):
    import cplex  
    import timeit
      
    
    c = cplex.Cplex()
    c.objective.set_sense(c.objective.sense.minimize)   

    # Adding variables to model
    # X_{j,k}: if job j is assigned after kth bin
    for j in range(1, Num_of_Jobs + 1):
            for k in range( Num_of_Jobs + 1, Num_of_Jobs+Num_of_B0+Num_of_B1 +Num_of_B2+ 1):
                varname = f"X_{j},{k}"
                c.variables.add(
                    lb=[0],
                    names=[varname],
                    types=c.variables.type.binary,
                    obj=[0.0],
                )

    # Adding Constraints:
    # Set 1: all jobs need to be delivered:
    for k in range(Num_of_Jobs+1,Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 + 1) :
                var = [None] * (Num_of_Jobs)
                coe = [None] * (Num_of_Jobs)
                h = 0
                for j in range(1, Num_of_Jobs + 1):
                        var[h] = f"X_{j},{k}"
                        coe[h] = float(e[j-1])
                        h = h + 1
                                                    
                if MP_Values[(k-1)*m+(AGV)]>0:
                    c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                    senses=["L"],
                    rhs=[BC],
                    )
                else:
                    c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                    senses=["L"],
                    rhs=[0.0],
                    )

    

    for j in range(1,Num_of_Jobs+1) :
            if MP_Values[(j-1)*m+AGV]>0:
                var = [None] * (Num_of_B0+Num_of_B1+Num_of_B2)
                coe = [None] * (Num_of_B0+Num_of_B1+Num_of_B2)
                h = 0
                for k in range(Num_of_Jobs+1, Num_of_Jobs + Num_of_B0+Num_of_B1+Num_of_B2+ 1):
                        var[h] = f"X_{j},{k}"
                        coe[h] = 1.0
                        h = h + 1
                c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                    senses=["E"],
                    rhs=[1],
                )


    
  #  c.write(f"A subproblem {AGV}.lp")
    c.parameters.mip.display.set(0)
    c.parameters.timelimit.set(Time)
    c.parameters.threads.set(Number_of_Thread)
   
    start = timeit.default_timer()
    c.solve()
    stop = timeit.default_timer()
    Running_Time = stop - start
    if c.solution.get_status()==101:
        return [True, Running_Time]
    elif c.solution.get_status()== 108:
        return [None,Running_Time] # Distinguishes the 104 status code
    else:
        return [False,Running_Time]

