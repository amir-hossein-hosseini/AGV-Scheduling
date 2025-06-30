# Function: Generating the CPLEX model of the Master problem of MILP2 (Different set of constraints can be deactive )

def MP_MILP2 (Num_of_Jobs,Num_of_B0,Num_of_B1,Num_of_B2,m,d,e,CT,BC,Given_LB=0, Given_UB=10000):
    import cplex
    import timeit
    import numpy as np

    

    ################################## set whch set of cinstraint should be considered 1 or relaxed 0 ##################################
    Each_Machine_Has_a_Bin=1
    Symmetry_Breaking=0
    Energy_Constraints=1
    Half_Jobs=1
    Lower_bound=1
    Upper_Bound=1
    Normal_Jobs_Are_Greater_than_Bins=1
    UB_on_Bins=0
    Delta_Constraint=0
    Symmetry_Breaking_for_AGV=0
    LB_on_Bins_from_Average=0
   ######################################################################################################################################



    c = cplex.Cplex()
    c.objective.set_sense(c.objective.sense.minimize)

    # Adding variables to model
    # X_{j,i}: if job j is assigned to AGV i
    for j in range(1, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 + 1):
        for i in range(1, m + 1):
            varname = f"X_{j},{i}"
            c.variables.add(
                lb=[0],
                names=[varname],
                types=c.variables.type.binary,
                )
                

    # C_{i}: completion time (last job's delivery time) of AGV i
    for i in range(1, m + 1):
        varname = f"C_{i}"
        c.variables.add(
            lb=[0], names=[varname], types=c.variables.type.integer
        )

    # C_Max
    c.variables.add(
         lb=[0], names=["C_Max"], obj=[1.0], types=c.variables.type.integer
    )

    # Adding objective function

  #  c.objective.set_linear("C_Max", 1)

    # Adding Constraints:
    # Set 1: all jobs need to be assigned to exactly one AGV:
    for j in range(1, Num_of_Jobs +Num_of_B0+Num_of_B1+ 1):
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
    



    # Set 2: Jobs in dummy bins can be assigned to at most one AGV:
    for j in range(Num_of_Jobs +Num_of_B0+Num_of_B1+1,Num_of_Jobs +Num_of_B0+Num_of_B1+Num_of_B2 + 1):
        var = [None] * (m )
        coe = [None] * (m )
        h = 0
        for i in range(1, m + 1):
                var[h] = f"X_{j},{i}"
                coe[h] = 1.0
                h = h + 1
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[1.0],
        )
    

    if Each_Machine_Has_a_Bin==1:
           # Set 3: Each AGV has exactly one bin from set B0
        for i in range(1, m + 1):
            var = [None] * (m )
            coe = [None] * (m )
            h = 0
            for j in range(Num_of_Jobs + 1 , Num_of_Jobs +Num_of_B0 +1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = 1.0
                    h = h + 1
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                senses=["E"],
                rhs=[1.0],
            )
    
    if Normal_Jobs_Are_Greater_than_Bins==1:
           # Set 4: Normal jobs assigned to each AGV are more than assigned bins
        for i in range(1, m + 1):
            var = [None] * (Num_of_Jobs +Num_of_B0+Num_of_B1+Num_of_B2  )
            coe = [None] * (Num_of_Jobs +Num_of_B0+Num_of_B1+Num_of_B2  )
            h = 0
            for j in range(1, Num_of_Jobs+1 ):
                var[h] = f"X_{j},{i}"
                coe[h] = 1.0
                h = h + 1
            for j in range(Num_of_Jobs + 1 , Num_of_Jobs +Num_of_B0 +Num_of_B1+Num_of_B2+1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = -1.0
                    h = h + 1
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                senses=["G"],
                rhs=[0.0],
            )



    # Set 5: Completion time:
    for i in range(1, m + 1):
        var = [None] * (Num_of_Jobs+Num_of_B1+Num_of_B2+1)
        coe = [None] * (Num_of_Jobs+Num_of_B1+Num_of_B2+1)
        h = 0
        for j in range(1, Num_of_Jobs+ 1):
                var[h] = f"X_{j},{i}"
                coe[h] = d[ j - 1]
                h = h + 1
        for j in range(Num_of_Jobs+Num_of_B0+1, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 +1):
                var[h] = f"X_{j},{i}"
                coe[h] = CT
                h = h + 1
        var[h] = f"C_{i}"
        coe[h] = -1.0
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=var, val=coe)],
            senses=["L"],
            rhs=[0.0],
        )
    
    
    # Set 6: Makespan calculation:

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



    if Energy_Constraints ==1:
    # Set 7: Energy constraint:
        for i in range(1, m + 1):
            var = [None] * (Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2)
            coe = [None] * (Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2)
            h = 0
            for j in range(1, Num_of_Jobs+ 1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = e[ j - 1]
                    h = h + 1
            for j in range(Num_of_Jobs+1, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 +1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = -BC
                    h = h + 1
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                senses=["L"],
                rhs=[0.0],
            )

    if LB_on_Bins_from_Average ==1:
    # Set 7: Energy constraint:
        for i in range(1, m + 1):
            var = [None] * (Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2)
            coe = [None] * (Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2)
            h = 0
            for j in range(1, Num_of_Jobs+ 1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = e[ j - 1]/BC
                    h = h + 1
            for j in range(Num_of_Jobs+1, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 +1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = -1
                    h = h + 1
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                senses=["L"],
                rhs=[0.0],
            )



    if  Symmetry_Breaking==1:
    # Set 8: Symmetry breaking:
        for j in range(Num_of_Jobs+Num_of_B0+2, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2+ 1):
            var = [None] * (2*m)
            coe = [None] * (2*m)
            h = 0
            for i in range(1, m+ 1):
                    var[h] = f"X_{j-1},{i}"
                    coe[h] = -1.0
                    h = h + 1
            for i in range(1, m+ 1):
                var[h] = f"X_{j},{i}"
                coe[h] = 1.0
                h = h + 1
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                senses=["L"],
                rhs=[0.0],
            )




# Set 9: Half jobs cannot be assigned together:
    if  Half_Jobs==1:
        J1=[]
        Size_of_J1=0
        J2=[]
        Size_of_J2=0
        J3=[]
        Size_of_J3=0
        J4=[]
        Size_of_J4=0
        J5=[]
        Size_of_J5=0
        J6=[]
        Size_of_J6=0

        for j in range(Num_of_Jobs):
            if e[j]> BC/2:
                    Size_of_J1=Size_of_J1+1
                    J1.append(j+1)
            elif e[j]==BC/2:
                    Size_of_J2=Size_of_J2+1
                    J2.append(j+1)
        
        for j in range(Num_of_Jobs):  
            if e[j]==BC/3:
                  Size_of_J3=Size_of_J3+1
                  J3.append(j+1)

            elif e[j]==2*BC/3:
                  Size_of_J4=Size_of_J4+1
                  J4.append(j+1)

            elif  BC/3 <e[j] and  e[j]< (2*BC)/3:
                  Size_of_J5=Size_of_J5+1
                  J5.append(j+1)
            
            elif e[j]> 2*BC/3:
                    Size_of_J6=Size_of_J6+1
                    J6.append(j+1)

                  
        print("Set of jobs in J1",J1)
        print("Set of jobs in J2",J2)
        print("Set of jobs in J3",J3)
        print("Set of jobs in J4",J4)
        print("Set of jobs in J5",J5)
        print("Set of jobs in J6",J6)



        if Size_of_J1 >0 or Size_of_J2>0:
            for i in range(1, m + 1):
                var = [None] * (Size_of_J1+Size_of_J2+Num_of_B0+Num_of_B1+Num_of_B2 )
                coe = [None] * (Size_of_J1+Size_of_J2+Num_of_B0+Num_of_B1+Num_of_B2 )
                h = 0
                for j in range(1, Num_of_Jobs+ 1):
                    if j in J1:
                        var[h] = f"X_{j},{i}"
                        coe[h] = 1
                        h=h+1
                    elif j in J2:
                        var[h] = f"X_{j},{i}"
                        coe[h] = 0.5
                        h=h+1       
                for j in range(Num_of_Jobs+1, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 +1):
                                var[h] = f"X_{j},{i}"
                                coe[h] = -1
                                h=h+1
                c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                    senses=["L"],
                    rhs=[0.0],
                    )             
                
        
        if Size_of_J3 >0 or Size_of_J4>0 or Size_of_J5>0 or Size_of_J6>0:
            for i in range(1, m + 1):
                var = [None] * (Size_of_J3+Size_of_J4+Size_of_J5+Size_of_J6+Num_of_B0+Num_of_B1+Num_of_B2)
                coe = [None] * (Size_of_J3+Size_of_J4+Size_of_J5+Size_of_J6+Num_of_B0+Num_of_B1+Num_of_B2)
                h = 0
                for j in range(1, Num_of_Jobs+ 1):
                    if j in J3:
                        var[h] = f"X_{j},{i}"
                        coe[h] = 0.33333333
                        h=h+1
                    elif j in J4:
                        var[h] = f"X_{j},{i}"
                        coe[h] = 0.6666666667
                        h=h+1     
                    elif j in J5:
                        var[h] = f"X_{j},{i}"
                        coe[h] = 0.5
                        h=h+1
                    elif j in J6:
                        var[h] = f"X_{j},{i}"
                        coe[h] = 1
                        h=h+1
       
                for j in range(Num_of_Jobs+1, Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2 +1):
                                var[h] = f"X_{j},{i}"
                                coe[h] = -1
                                h=h+1
                c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                    senses=["L"],
                    rhs=[0.0],
                    )                    


# Set 10: C_{max}> LB
    if  Lower_bound==1:
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=[f"C_Max"], val=[1.0])],
            senses=["G"],
            rhs=[Given_LB],
            )   


# Set 11: C_{max}< UB
    if  Upper_Bound==1:
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=[f"C_Max"], val=[1.0])],
            senses=["L"],
            rhs=[Given_UB],
            )             
       
        





# Set 13: Number of assigned bins and jobs must be proportional with respect to delta
    
    if Delta_Constraint==1:
          # Compute delta: the maximum number of normal jobs wich can be carried by a recharging operation
        Sorted_e=sorted(e)    
        SUM=0
        delta=0
        for j in range(Num_of_Jobs):
            if Sorted_e[j]+SUM<= BC:
                SUM=Sorted_e[j]+SUM
                delta=delta+1
            else:
                break
        
        print(" sorted energy consumption of jobs, and delta")
        print(Sorted_e)
        print(delta)


        for i in range(1, m + 1):
            var = [None] * (Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2)
            coe = [None] * (Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2)
            h = 0
            for j in range(1,Num_of_Jobs+1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = 1.0
                    h = h + 1
            for j in range(Num_of_Jobs+1,Num_of_Jobs+Num_of_B0+Num_of_B1+Num_of_B2+1):
                    var[h] = f"X_{j},{i}"
                    coe[h] = -delta
                    h = h + 1
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                senses=["L"],
                rhs=[0.0],
            )


# Set 14: Symmetry breaking for AGVs, a job is asigned to an AGV only if, at least one of its preceding job is assigned to one of the previous AGVs.
    if Symmetry_Breaking_for_AGV==1:
        for j in range(1,m+1):
                    c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=[f"X_{j},{j}"], val=[1.0])],
                    senses=["E"],
                    rhs=[1],
                )

        for j in range (m+1, Num_of_Jobs+1):
            for i in range(2, m + 1):
                var = [None] * (j)
                coe = [None] * (j)
                h = 0
                var[h] = f"X_{j},{i}"
                coe[h] = 1.0
                h = h + 1
                for jj in range(1, j):
                    var[h] = f"X_{jj},{i-1}"
                    coe[h] = -1
                    h = h + 1
                c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=var, val=coe)],
                    senses=["L"],
                    rhs=[0.0],
                )          

    c.write("AAA_MP of MILP2 .lp")
  
    return c