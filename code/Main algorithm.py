
# Solving the instances by Single-Tree Serach Logic Based Benders Decomposition (STSLBDD)  
import cplex
import cplex.exceptions
import numpy as np
import os
import math
from BPP import *
from Pm import *
from Pm_for_UB import *
from Class_STSLBDD  import bendersagvscheduling
from Class_STSLBDD_Just_FCF import bendersagvscheduling_Just_FCF
from Decoding import *



list1 = [2, 5, 10]
list2 = [50, 100, 150, 200]
list3 = [10, 20, 30]
list4 = [1, 2, 4]
list5 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

########################################## Inputs ##############################################################
Overall_Time_Limit=3600                       # corresponds to the "Overall_Time_Limit" in the algorithm
Time_for_CBPP1=1                              # corresponds to the "Inner_Time_Limit 1" in the algorithm
Time_for_CBPP2=10                             # corresponds to the "Inner_Time_Limit 2" in the algorithm
Time_for_FCF=60                               # corresponds to the "Inner_Time_Limit 3" in the algorithm
Time_for_Making_Final_Feasible_Solution=0     # corresponds to the "Extra_Time_Limit" in the algorithm
Time_Limit_BPP=600                            # corresponds to the "Time_Limit_BPP" in the algorithm
Time_Limit_Pm=600                             # corresponds to the "Time_Limit_Pm" in the algorithm
Time_Limit_UB=600                             # corresponds to the "Time_Limit_UB" in the algorithm
Number_of_Thread=8                            # Number of CPU threads used by the algorithm

CBPP_Varsion=1                                # If the LBBD (CBPP) variant is used
FBPP_Version=0                                # If the LBBD (FBPP) variant is used
#################################################################################################################

########################################## Read the data of the instance ############################################
for J in list2:
    for V in list1:
        for T in list3:
            for W in list4:
                for Q in list5:
                    try:
                        m = V
                        n = J
                        tt = np.zeros((n, m))
                        ec = np.zeros((n, m))
                        CT = 60
                        BC = 10
            
                        text = open(f"Ins_V{V}_J{J}_T{T}_R60_B10_W{W} ({Q}).txt", "r")

                        for i, line in enumerate(text):
                            if i >= 2 and i <= n + 1:
                                a = line.strip()
                                b = np.matrix(a)
                                tt[i - 2, :] = np.matrix(b)
                        text.close()
                        d= tt[:,0]

                        text = open(f"Ins_V{V}_J{J}_T{T}_R60_B10_W{W} ({Q}).txt", "r")

                        for i, line in enumerate(text):
                            if i >= n + 4 and i <= 2 * n + 3:
                                ec[i - n - 4, :] = np.matrix(line.strip())
                        text.close()
                        e= ec[:,0]

                                           
                        index= [50, 100, 150, 200].index(J)*270 + [2, 5, 10].index(V)*90  + [10, 20, 30].index(T)*30 + [1, 2, 4].index(W)*10 +Q
                        if index >=1:
               
########################################## Preprocessing  ############################################
                            # Step 1: Compute LB_swaps by solving the corresponding bin packing problem
                            [LB_swaps, Z_BPP, X_BPP, Gap_of_BPP, Running_Time_of_BPP] = BPP(n, e, Time_Limit_BPP, b)          


                            # Step 2: Compute LB_init by solving the corresponding parallel machine problem
                            Num_of_Bins = math.ceil(LB_swaps) - m
                            d1 = [None] * (n + int(Num_of_Bins))
                            for j in range(n + int(Num_of_Bins)):
                                if j <= n - 1:
                                    d1[j] = int(d[j])
                                else:
                                    d1[j] = CT
                            n1 = n + int(Num_of_Bins)

                            [LB_init, UB_Pm, AJ, Number_of_assigned_jobs, Gap_of_Pm, Running_Time_of_Pm] = Pm(n1, m, d1, Time_Limit_Pm)  


                           # Step 3: Compute the UB_init and (x_init, Z_init)  by solving the special parallel machine problem 
                            if Z_BPP <= m:
                                Assignemt_of_bins_to_AGVs = [None] * int(Z_BPP)
                                for i in range(int(Z_BPP)):
                                    Assignemt_of_bins_to_AGVs[i] = 1
                                UB_on_CT_AGVs = max(Tranportation_Time_Inside_Each_Bin)
                                LB_on_CT_AGVs = max(Tranportation_Time_Inside_Each_Bin)
                                Assignemt_of_bins_to_AGVs = []
                                Running_Time_of_SPm = 0
                                Gap_of_SPm = 0

                            elif Z_BPP > m:
                                Tranportation_Time_Inside_Each_Bin = [j + 60 for j in Tranportation_Time_Inside_Each_Bin]
                                print(Tranportation_Time_Inside_Each_Bin)

                                [LB_on_CT_AGVs,UB_init,X_init,Z_init,Gap_of_SPm,Running_Time_of_SPm] = Pm_for_UB(int(Z_BPP), m, Tranportation_Time_Inside_Each_Bin, CT, Time_Limit_UB ) 


                            Preprocessing_Time = Running_Time_of_BPP + Running_Time_of_Pm + Running_Time_of_SPm
                            Running_Time= Overall_Time_Limit - Preprocessing_Time 
                            
                            
                            # Step 4: set the values of J^n, J_0^b,  J_1^b and J_2^b
                            Num_of_Jobs=n
                            Num_of_B0=m
                            if int(LB_swaps)>m:
                                Num_of_B1=int(LB_swaps)-m
                            else:
                                Num_of_B1=0
                            Num_of_B2=m*4

                            if   UB_init==UB_init:
                                print("THe instance is solved in the preprocessening phase ")
                                print("The best found objecetive value (LB)             %d"% UB_init)
                                print("The best feasible solution (UB)                  %d"% UB_init)
                                print('The running time of the algorithm:               %d'% Preprocessing_Time)
                                print("Variables value:                                  ")
                                print("Number of jobs/bins assigned to each AGV          ",Z_init)
                                print("Variables' values (assignments of jobs/bins to the AGVs)")
                                print(X_init)

                            else:
########################################## Perform the LBBD algorithm  ############################################
                                if CBPP_Varsion==1:
                                    [LB, UB, Gap,Running_Time, Var_Array, Status, Num_Nodes, Num_Cuts, Number_of_Feasibilty_Cut,Number_of_Combinatorial_Cut,Number_of_Analytical_Explanation_Cut,Number_of_No_Good_Explanation_Cut,Number_of_Iteration,Number_of_CBPP2_Check_Recalled,Number_of_Feasibility_Check_Recalled,If_LBBD_Exits_With_No_Feasible_Solution,Number_of_Cases_FCF_Exits_Because_of_Timelimit,Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit,Elapsed_Time_on_Feasiblity_Check,Elapsed_Time_on_Cuts,If_LBBD_Exits_With_No_Found_Node,Spent_Time_on_Final_Heuristic,If_Initial_UB_Is_Reported,If_UB_From_Open_Problems_Is_Reported] = bendersagvscheduling(Num_of_Jobs,Num_of_B0, Num_of_B1,Num_of_B2,m, d,e,CT,BC,Running_Time,T,W,Q,Number_of_Thread,LB_init,UB_init,Time_for_FCF,Time_for_CBPP1,Time_for_CBPP2,Time_for_Making_Final_Feasible_Solution)
                                
                                if FBPP_Version==1:
                                    [LB, UB, Gap,Running_Time, Var_Array, Status, Num_Nodes, Num_Cuts, Number_of_Feasibilty_Cut,Number_of_Combinatorial_Cut,Number_of_Iteration,Number_of_CBPP2_Check_Recalled,Number_of_Feasibility_Check_Recalled,If_LBBD_Exits_With_No_Feasible_Solution,Number_of_Cases_FCF_Exits_Because_of_Timelimit,Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit,Elapsed_Time_on_Feasiblity_Check,Elapsed_Time_on_Cuts,If_LBBD_Exits_With_No_Found_Node,Spent_Time_on_Final_Heuristic,If_Initial_UB_Is_Reported,If_UB_From_Open_Problems_Is_Reported] = bendersagvscheduling_Just_FCF(Num_of_Jobs,Num_of_B0, Num_of_B1,Num_of_B2,m, d,e,CT,BC,Running_Time,T,W,Q,Number_of_Thread,LB_init,UB_init,Time_for_FCF,Time_for_CBPP1,Time_for_CBPP2,Time_for_Making_Final_Feasible_Solution)

                                print("The best found objecetive value (LB)             %d"% LB)
                                print("The best feasible solution (UB)                  %d"% UB)
                                print("The optimality gap                             ",Gap)
                                print('The running time of the algorithm:               %d'% Running_Time)
                                print("Active user cuts/lazy constraints:               %d"% Num_Cuts)
                                print("Number of applied feasibility cuts:              %d"% Number_of_Feasibilty_Cut)
                                print("Number of applied combinatorial cuts:            %d"% Number_of_Combinatorial_Cut)
                                print("Number of analytical explanation-based cuts:     %d"% Number_of_Analytical_Explanation_Cut)
                                print("Number of no-good explanation-based cuts:        %d"% Number_of_No_Good_Explanation_Cut)
                                print("Number of performed iterations:                  %d"% Number_of_Iteration)
                                print("Variables value:                                  ")
                                [Number_of_assigned_jobs, Solution] = Decoding( m,Num_of_Jobs,Num_of_B0,Num_of_B1,Num_of_B2,Var_Array,)                           
                                print("Number of jobs/bins assigned to each AGV          ",Number_of_assigned_jobs,)
                                print("Variables' values (assignments of jobs/bins to the AGVs)")
                                print(Solution)

                            pass

                    except cplex.exceptions.CplexSolverError as e:
                        print(f"CPLEX Solver Error: {e}")  # Print the error message
                    continue  # Skip to the next instance