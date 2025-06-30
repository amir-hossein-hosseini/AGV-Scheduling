import sys
import traceback
import cplex
import timeit
import time
from MP_MILP2 import *
from SP_Feasibility_Check import *
from Decoding import *
from generate_decision_variable_list import *
from Generate_Subsets import *
from Compute_Completion_Time import *
import os
from CBPP import *
from Make_Feasible_Solution import *

class MyLazyConstraintCallback:
    """This is the class implementing the generic callback interface.
    lazy_constraint: adds the feasibility cuts as a lazy constraint.
    """

    def __init__(self, m, num_jobs, num_b0, num_b1, num_b2, d, e, t, b, Given_UB, T, W, Q,Time_for_FCF,Time_for_CBPP1,Time_for_CBPP2,Time_for_MIS_FCF,Time_for_MIS_CBPP,Number_of_Thread):
        self.m = m
        self.num_jobs = num_jobs
        self.num_b0 = num_b0
        self.num_b1 = num_b1
        self.num_b2 = num_b2
        self.d = d
        self.e = e
        self.b = b
        self.t = t
        self.Given_UB = Given_UB
        self.T = T
        self.W = W
        self.Q = Q
        self.Time_for_FCF=Time_for_FCF
        self.Time_for_CBPP1=Time_for_CBPP1
        self.Time_for_CBPP2=Time_for_CBPP2
        self.Number_of_Thread=Number_of_Thread
        self.Time_for_MIS_FCF=Time_for_MIS_FCF
        self.Time_for_MIS_CBPP=Time_for_MIS_CBPP
        self.iteration = 0
        self.Feasibility_Check_Recalled=0
        self.CBPP2_Recalled=0
        self.last_explored_node=None
        self.Aggregated_Time_for_Cuts=0
        self.Aggregated_Time_for_MIS=0
        self.Aggregated_Time_for_Feasibility_Check=0
        self.Problamatic_Nodes = []
        self.Problematic_Values=[]


    Number_of_Feasibilty_Cut = 0
    Number_of_MIS_Combinatorial_Cut = 0
    Number_of_Cases_FCF_Exits_Because_of_Timelimit=0
    Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit=0
    Last_Feasible_Node=[]
    Last_Value_of_Node=[]

    def lazy_constraint(self,context,Feasibility_Cut=1,Combinatorial_Cuts=1):
        """Lazy constraint callback to enforce the infeasible assignments.
        The callback is invoked for every integer feasible solution CPLEX finds.

        For each infeasible assignment to the machines, a constraint as follow is added (feasibility cut):
           \sum_{j \in J^b} X_{ji} \geq  |J^b_i| +1 - (|J_{i}^n| -\sum_{j \in J_{i}^n} X_{ji})* M  \forall i \in I


        Besides, for each infeasible assignment to the machines, whose competion time + t exceeds a given UB, a constraint as follow is added (combinatorial cut):
            \sum_{j \in J_{i}^n} X_{ji} \leq  |J_{i}^n| -1  \forall i \in I


        # Raise an exception if the current node renders unboundness """
        if not context.is_candidate_point():
            raise Exception("Unbounded solution")

        # Generate the list of the variables' name (used in the added cuts) """
        List_of_DV = generate_decision_variable_list((self.num_jobs + self.num_b0 + self.num_b1 + self.num_b2), self.m)
        self.Last_Feasible_Node=context.get_candidate_point()
        self.Last_Value_of_Node=context.get_candidate_objective()
        Current_Solution = context.get_candidate_point()
        [Number_of_assigned_jobs, Initial_AJ] = Decoding(self.m,self.num_jobs,self.num_b0,self.num_b1,self.num_b2,context.get_candidate_point())

        self.iteration = self.iteration + 1
        List_of_AGVs_with_Unclear_Status_in_the_First_Loop=[]
        List_of_AGVs_with_Unclear_Status_in_the_Second_Loop=[]
        If_Feasibilty_of_an_Iteration_Cannot_Be_Checked_From_FCF=0

        ##############################################  Check feasibility of the assignments and add possible cuts ##############################################
        Start_Time_for_Feasibility_Check= time.time()
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",Start_Time_for_Feasibility_Check)
        
        ############# Loop 1- FBPP in Time_for_CBPP1 seconds ###############
        for machine in range(self.m):
            print(f"__________________________________ FCF1: iteration {self.iteration}, AGV {machine+1} with makespan of : __________________________________________")
            print(context.get_candidate_objective())
            List_of_Assigned_Jobs_to_This_AGV = Initial_AJ[machine][:]
            print(f"__________________________________ List of assigned jobs to AGV {machine+1}: {List_of_Assigned_Jobs_to_This_AGV} ____________________________________________________")
           
            [is_feasible, Time_of_FCF1] = SP_Feasibility_Check(self.num_jobs,self.num_b0,self.num_b1,self.num_b2,self.m,machine,self.e,self.b,Current_Solution,self.Time_for_CBPP1,self.Number_of_Thread)
            print(f"Feasibilty time 1 of the instance at iteration {self.iteration} took {Time_of_FCF1} seconds  ")
            if is_feasible is True:
                print(f"+++++++++++++++++++++++++++++++++ FCF1={is_feasible} +++++++++++++++++++++++++++")
                continue
                
            elif is_feasible is False:
                print(f"------------------------------- FCF1={is_feasible} -------------------------------")
                if Feasibility_Cut == 1 or Combinatorial_Cuts == 1:
                    Start_Time_for_Cut = time.time()
                    ##############################################  Adding fesiblity cuts ##############################################
                    if Feasibility_Cut == 1:
                        self.Number_of_Feasibilty_Cut = self.Number_of_Feasibilty_Cut + 1
                        print(f"++++++++++++++++++++++ Simple Feasibilty Cut on {List_of_Assigned_Jobs_to_This_AGV} +++++++++++++++++++++++")
                        cut_lhs, sense, cut_rhs = self.create_feasibility_cut(machine, context.get_candidate_point())
                        for machine_index in range(self.m):
                            constraint_for_rejection = cplex.SparsePair(ind=List_of_DV, val=cut_lhs[machine_index][:])
                            constraints_for_rejection = [constraint_for_rejection]
                            context.reject_candidate(constraints=constraints_for_rejection,senses=sense,rhs=[cut_rhs])
                            # Output the cut as a LP file: """
                        #      self.save_feasibility_cut_to_lp_file(List_of_DV,cut_lhs[machine_index][:],sense,cut_rhs,f"Added_feasibility_cuts for instance {self.m}-{self.num_jobs}-{self.T}-{self.W}-{self.Q}.txt")

                    ##############################################  Adding combinatorial cuts ##############################################
                    if Combinatorial_Cuts == 1:
                        if (Compute_Completion_Time(Initial_AJ[machine][:],self.d,self.e,self.num_jobs,self.num_b0,self.t,self.b,)+ self.t>= self.Given_UB):
                            self.Number_of_Combinatorial_Cut = (self.Number_of_Combinatorial_Cut + 1)
                            print(f"++++++++++++++++++++++ Simple Combinatorial Cut on {List_of_Assigned_Jobs_to_This_AGV} +++++++++++++++++++++++")

                            cut_lhs, sense, cut_rhs = self.create_combinatorial_cut(machine, context.get_candidate_point())
                            for machine_index in range(self.m):
                                constraint_for_rejection = cplex.SparsePair(ind=List_of_DV, val=cut_lhs[machine_index][:])
                                constraints_for_rejection = [constraint_for_rejection]
                                context.reject_candidate(constraints=constraints_for_rejection,senses=sense,rhs=[cut_rhs],)


                    End_Time_for_Cut = time.time()
                    self.Aggregated_Time_for_Cuts=self.Aggregated_Time_for_Cuts+End_Time_for_Cut-Start_Time_for_Cut
                    print(f"____________________________ Spent Time for Simple Cuts: {self.Aggregated_Time_for_Cuts}__________________________________")
                    print(f"____________________________ Cuts have been added at iteration {self.iteration}, AGV {machine+1} and the node is terminated ___________________________________________")
                    List_of_AGVs_with_Unclear_Status_in_the_First_Loop=[]
                break
                
            elif is_feasible is None:
                print(" ************************************ FCF1 couldn't be checked in the given time limit ************************************ ")
                List_of_AGVs_with_Unclear_Status_in_the_First_Loop.append(machine)
                print(f"List of AGVs with not clear status in the first loop, when FCF1 is solve in {self.Time_for_CBPP1} seconds ")
                print(List_of_AGVs_with_Unclear_Status_in_the_First_Loop)
            
        ####### Loop 2- FBPP in Time_for_CBPP2 seconds ###############
        print(f"_____________________________________ Status of AGVs {List_of_AGVs_with_Unclear_Status_in_the_First_Loop} couldn't be determined from CBPP1 in {self.Time_for_CBPP1} at iteration {self.iteration} ____________________________________________*")
        print(List_of_AGVs_with_Unclear_Status_in_the_First_Loop)
        print(len(List_of_AGVs_with_Unclear_Status_in_the_First_Loop))

        if len(List_of_AGVs_with_Unclear_Status_in_the_First_Loop)>0:
            self.CBPP2_Recalled=self.CBPP2_Recalled+1
            for machine in List_of_AGVs_with_Unclear_Status_in_the_First_Loop:
                print(f"__________________________________________ FCF 2: iteration {self.iteration}, AGV {machine+1}: __________________________________________")
                List_of_Assigned_Jobs_to_This_AGV = Initial_AJ[machine][:]
                print(f"__________________________________________ List of assigned jobs to AGV {machine+1}: {List_of_Assigned_Jobs_to_This_AGV} __________________________________________")
                [is_feasible, Time_of_FCF2] = SP_Feasibility_Check(self.num_jobs,self.num_b0,self.num_b1,self.num_b2,self.m,machine,self.e,self.b,Current_Solution,self.Time_for_CBPP2,self.Number_of_Thread)
                print(f"Feasibilty time 2 of the instance at iteration {self.iteration} took {Time_of_FCF2} seconds  ")
                if is_feasible is True:
                    print(f"+++++++++++++++++++++++++++++++++ FCF2={is_feasible} +++++++++++++++++++++++++++")
                    continue
                    
                elif is_feasible is False:
                    print(f"------------------------------- FCF2={is_feasible} -------------------------------")
                    if Feasibility_Cut == 1 or Combinatorial_Cuts == 1:
                        Start_Time_for_Cut = time.time()
                        ##############################################  Adding fesiblity cuts ##############################################
                        if Feasibility_Cut == 1:
                            self.Number_of_Feasibilty_Cut = self.Number_of_Feasibilty_Cut + 1
                            print(f"++++++++++++++++++++++ Simple Feasibilty Cut on {List_of_Assigned_Jobs_to_This_AGV} +++++++++++++++++++++++")
                            cut_lhs, sense, cut_rhs = self.create_feasibility_cut(machine, context.get_candidate_point())
                            for machine_index in range(self.m):
                                constraint_for_rejection = cplex.SparsePair(ind=List_of_DV, val=cut_lhs[machine_index][:])
                                constraints_for_rejection = [constraint_for_rejection]
                                context.reject_candidate(constraints=constraints_for_rejection,senses=sense,rhs=[cut_rhs])

                        ##############################################  Adding combinatorial cuts ##############################################
                        if Combinatorial_Cuts == 1:
                            if (Compute_Completion_Time(Initial_AJ[machine][:],self.d,self.e,self.num_jobs,self.num_b0,self.t,self.b,)+ self.t>= self.Given_UB):
                                self.Number_of_Combinatorial_Cut = (self.Number_of_Combinatorial_Cut + 1)
                                print(f"++++++++++++++++++++++ Simple Combinatorial Cut on {List_of_Assigned_Jobs_to_This_AGV} +++++++++++++++++++++++")

                                cut_lhs, sense, cut_rhs = self.create_combinatorial_cut(machine, context.get_candidate_point())
                                for machine_index in range(self.m):
                                    constraint_for_rejection = cplex.SparsePair(ind=List_of_DV, val=cut_lhs[machine_index][:])
                                    constraints_for_rejection = [constraint_for_rejection]
                                    context.reject_candidate(constraints=constraints_for_rejection,senses=sense,rhs=[cut_rhs],)


                        End_Time_for_Cut = time.time()
                        self.Aggregated_Time_for_Cuts=self.Aggregated_Time_for_Cuts+End_Time_for_Cut-Start_Time_for_Cut
                        print(f"____________________________ Spent Time for Simple Cuts: {self.Aggregated_Time_for_Cuts}__________________________________")
                        print(f"____________________________ Cuts have been added at iteration {self.iteration}, AGV {machine+1} and the node is terminated ___________________________________________")
                        List_of_AGVs_with_Unclear_Status_in_the_Second_Loop=[]
                    break
                    
                elif is_feasible is None:
                    print(f" ************************************ The FCF2 can't be solved in  {self.Time_for_CBPP2} seconds for AGV {machine+1} at iteration {self.iteration} ************************************ ")
                    List_of_AGVs_with_Unclear_Status_in_the_Second_Loop.append(machine)
                    print(f"List of AGVs with not clear status in the second loop, when FCF2 is solve in {self.Time_for_CBPP2} seconds: ")
                    print(List_of_AGVs_with_Unclear_Status_in_the_Second_Loop)
        
        print(List_of_AGVs_with_Unclear_Status_in_the_Second_Loop)
        print(len(List_of_AGVs_with_Unclear_Status_in_the_Second_Loop))

        ####### Loop 3- FCF in Time_for_FCF seconds ###############
        if len(List_of_AGVs_with_Unclear_Status_in_the_Second_Loop)>0:
            self.Feasibility_Check_Recalled=self.Feasibility_Check_Recalled+1
            
            for machine in List_of_AGVs_with_Unclear_Status_in_the_Second_Loop:
                print("_____________________________________ FEASIBILITY CHECK FUNCTION 3 (FCF) ____________________________________________*")
                [is_feasible, Time_of_FCF] = SP_Feasibility_Check(self.num_jobs,self.num_b0,self.num_b1,self.num_b2,self.m,machine,self.e,self.b,Current_Solution,self.Time_for_FCF,self.Number_of_Thread)
                print(f"Feasibilty time 3 of the instance at iteration {self.iteration} took {Time_of_FCF} seconds  ")
                if is_feasible is True:
                    print(f"+++++++++++++++++++++++++++++++++ FCF={is_feasible} +++++++++++++++++++++++++++")
                    continue
                
                elif is_feasible is False:
                    print(f"------------------------------- FCF={is_feasible} -------------------------------")
                    if Feasibility_Cut == 1 or Combinatorial_Cuts == 1:
                        Start_Time_for_Cut = time.time()

                        ##############################################  Adding fesiblity cuts ##############################################
                        if Feasibility_Cut == 1:
                            self.Number_of_Feasibilty_Cut = self.Number_of_Feasibilty_Cut + 1
                            print(f"++++++++++++++++++++++ Simple Feasibilty Cut on {List_of_Assigned_Jobs_to_This_AGV} +++++++++++++++++++++++")
                            cut_lhs, sense, cut_rhs = self.create_feasibility_cut(machine, context.get_candidate_point())
                            for machine_index in range(self.m):
                                constraint_for_rejection = cplex.SparsePair(ind=List_of_DV, val=cut_lhs[machine_index][:])
                                constraints_for_rejection = [constraint_for_rejection]
                                context.reject_candidate(constraints=constraints_for_rejection,senses=sense,rhs=[cut_rhs])

                        ##############################################  Adding combinatorial cuts ##############################################
                        if Combinatorial_Cuts == 1:
                            if (Compute_Completion_Time(Initial_AJ[machine][:],self.d,self.e,self.num_jobs,self.num_b0,self.t,self.b,)+ self.t>= self.Given_UB):
                                self.Number_of_Combinatorial_Cut = (self.Number_of_Combinatorial_Cut + 1)
                                print(f"++++++++++++++++++++++ Simple Combinatorial Cut on {List_of_Assigned_Jobs_to_This_AGV} +++++++++++++++++++++++")

                                cut_lhs, sense, cut_rhs = self.create_combinatorial_cut(machine, context.get_candidate_point())
                                for machine_index in range(self.m):
                                    constraint_for_rejection = cplex.SparsePair(ind=List_of_DV, val=cut_lhs[machine_index][:])
                                    constraints_for_rejection = [constraint_for_rejection]
                                    context.reject_candidate(constraints=constraints_for_rejection,senses=sense,rhs=[cut_rhs],)


                        End_Time_for_Cut = time.time()
                        self.Aggregated_Time_for_Cuts=self.Aggregated_Time_for_Cuts+End_Time_for_Cut-Start_Time_for_Cut
                        print(f"____________________________ Spent Time for Simple Cuts: {self.Aggregated_Time_for_Cuts}__________________________________")

                    If_Feasibilty_of_an_Iteration_Cannot_Be_Checked_From_FCF=0
                    break
                
                elif is_feasible is None:
                    print(" !!!!!!!!!!!!!!!!!!!  FCF couldn't be checked in the given time limit !!!!!!!!!!!!!!!!!!!")
                    If_Feasibilty_of_an_Iteration_Cannot_Be_Checked_From_FCF=1
                
                    
            
            if If_Feasibilty_of_an_Iteration_Cannot_Be_Checked_From_FCF==1:
                self.Number_of_Cases_FCF_Exits_Because_of_Timelimit=self.Number_of_Cases_FCF_Exits_Because_of_Timelimit+1
                self.Problamatic_Nodes.append(context.get_candidate_point())
                self.Problematic_Values.append(context.get_candidate_objective())
                context.reject_candidate()

        End_Time_for_Feasibility_Check= time.time()
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",End_Time_for_Feasibility_Check)
        self.Aggregated_Time_for_Feasibility_Check=self.Aggregated_Time_for_Feasibility_Check+End_Time_for_Feasibility_Check-Start_Time_for_Feasibility_Check
        print(f"____________________________ Spent Time for Feasiblity check and [MIS] Cuts: {self.Aggregated_Time_for_Feasibility_Check}__________________________________")

    def create_feasibility_cut(self, machine, current_solution):
        Big_M = self.num_b0 + self.num_b1 + self.num_b2
        cut_lhs = [[0]* ((self.num_jobs + self.num_b0 + self.num_b1 + self.num_b2) * self.m+ self.m+ 1) for _ in range(self.m)]

        Num_of_Assigned_Jobs_to_AGV = 0
        for job_index in range(self.num_jobs):
            if current_solution[job_index * self.m + machine] > 0:
                Num_of_Assigned_Jobs_to_AGV += 1
                for machine_index in range(self.m):
                    cut_lhs[machine_index][job_index * self.m + machine_index] = -Big_M

        Num_of_Assigned_Bins_to_AGV = 0
        for bin_index in range(
            self.num_jobs, self.num_jobs + self.num_b0 + self.num_b1 + self.num_b2):
            if current_solution[bin_index * self.m + machine] > 0:
                Num_of_Assigned_Bins_to_AGV += 1
            for machine_index in range(self.m):
                cut_lhs[machine_index][bin_index * self.m + machine_index] = 1.0

        cut_rhs = (Num_of_Assigned_Bins_to_AGV - (Big_M * Num_of_Assigned_Jobs_to_AGV) + 1)
        sense = "G"
        return cut_lhs, sense, cut_rhs



    def create_combinatorial_cut(self, machine, current_solution):
        cut_lhs = [[0]* ((self.num_jobs + self.num_b0 + self.num_b1 + self.num_b2) * self.m+ self.m+ 1) for _ in range(self.m)]

        Num_of_Assigned_Jobs_to_AGV = 0
        for job_index in range(self.num_jobs):
            if current_solution[job_index * self.m + machine] > 0:
                Num_of_Assigned_Jobs_to_AGV += 1
                for machine_index in range(self.m):
                    cut_lhs[machine_index][job_index * self.m + machine_index] = +1

        cut_rhs = Num_of_Assigned_Jobs_to_AGV - 1
        sense = "L"

        return cut_lhs, sense, cut_rhs
    

    



    def invoke(self, context):
        """
        This is the method that we have to implement to fulfill the generic callback contract. CPLEX will call this method during
        the solution process at the places that we asked for.
        """
        try:
            if context.in_candidate():
                self.lazy_constraint(context,Feasibility_Cut=1,Combinatorial_Cuts=1)
        except:
            info = sys.exc_info()
            print("#### Exception in callback: ", info[0])
            print("####                        ", info[1])
            print("####                        ", info[2])
            traceback.print_tb(info[2], file=sys.stdout)
            raise


def bendersagvscheduling_Just_FCF(num_jobs,num_b0,num_b1,num_b2,m,d,e,t,b,Time,T,V,Q,Number_of_Thread,Given_LB=0,Given_UB=10000,Time_for_FCF=60,Time_for_CBPP1=1,Time_for_CBPP2=10,Time_for_Making_Final_Feasible_Solution=3600):
 
    """Solve an AGV scheduling problem with cutting planes using the new generic callback interface."""

    # Create the model
    cpx = MP_MILP2(num_jobs,num_b0,num_b1,num_b2,m,d,e,t,b,Given_LB,Given_UB)

    """ Tweak some CPLEX parameters so that CPLEX has a harder time to  solve the model and our cut separators can actually kick in. """
    cpx.parameters.mip.display.set(2)
    cpx.parameters.threads.set(Number_of_Thread)
    cpx.parameters.preprocessing.presolve.set(0)


    # Setup the callback.
    # We instantiate the callback object and attach the necessary data to it.
    # We also setup the contexmask parameter to indicate when the callback should be called.
    agvschedulingcuts= MyLazyConstraintCallback(m, num_jobs, num_b0, num_b1, num_b2, d, e, t, b, Given_UB, T, V, Q, Time_for_FCF ,Time_for_CBPP1,Time_for_CBPP2,Number_of_Thread )
    contextmask = 0
    contextmask |= cplex.callbacks.Context.id.candidate

    # If contextMask is not zero we add the callback.
    if contextmask:
        cpx.set_callback(agvschedulingcuts, contextmask)

    # Inializing the model and cplex input

    start = timeit.default_timer()
    cpx.parameters.timelimit.set(Time)
   
  ### In case that an initial solution is given to the model, last two lines must be unmarked. 
   # indices = list(range(len(Initial_Solution)))  # Indices of the variables
   # cpx.MIP_starts.add(cplex.SparsePair(ind=indices, val=Initial_Solution), cpx.MIP_starts.effort_level.solve_MIP)

    cpx.solve()
    stop = timeit.default_timer()

    try:
        Running_Time = stop - start  
        Number_of_Feasibilty_Cut=agvschedulingcuts.Number_of_Feasibilty_Cut
        Number_of_Combinatorial_Cut=agvschedulingcuts.Number_of_Combinatorial_Cut
        Number_of_Iteration=agvschedulingcuts.iteration
        Number_of_Cases_FCF_Exits_Because_of_Timelimit=agvschedulingcuts.Number_of_Cases_FCF_Exits_Because_of_Timelimit
        Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit=agvschedulingcuts.Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit
        Number_of_CBPP2_Check_Recalled=agvschedulingcuts.CBPP2_Recalled
        Number_of_Feasibility_Check_Recalled=agvschedulingcuts.Feasibility_Check_Recalled        
        Elapsed_Time_on_Feasiblity_Check=agvschedulingcuts.Aggregated_Time_for_Feasibility_Check
        Elapsed_Time_on_Cuts=agvschedulingcuts.Aggregated_Time_for_Cuts
        Elapsed_Time_on_MIS=agvschedulingcuts.Aggregated_Time_for_MIS
        Last_Feasible_Node=agvschedulingcuts.Last_Feasible_Node
        Number_of_Cases_FCF_Exits_Because_of_Timelimit=agvschedulingcuts.Number_of_Cases_FCF_Exits_Because_of_Timelimit
        Problamatic_Nodes=agvschedulingcuts.Problamatic_Nodes
        Problematic_Values=agvschedulingcuts.Problematic_Values
        If_LBBD_Exits_With_No_Found_Feasible_Solution=0 
        If_LBBD_Exits_With_No_Found_Node=0
        Spent_Time_on_Final_Heuristic=0
        If_Initial_UB_Is_Reported=1
        If_UB_From_Open_Problems_Is_Reported=0
        LB = Given_LB
        UB = Given_UB
        Gap = (UB-LB)/UB
        Running_Time=stop-start
        Optimal_Schedule=[1 for _ in range(num_jobs*m+(num_b0+num_b1+num_b2)*m+m+1)]
        
        if len(Last_Feasible_Node)==0 and Number_of_Cases_FCF_Exits_Because_of_Timelimit==0:
            print("No solution has been found for the master problem, i.e., the master problem cannot be solved")
            If_LBBD_Exits_With_No_Found_Feasible_Solution=1   
            If_LBBD_Exits_With_No_Found_Node=1


            
        elif len(Last_Feasible_Node)==0 and Number_of_Cases_FCF_Exits_Because_of_Timelimit>0 and Time_for_Making_Final_Feasible_Solution>0:
            print("No solution has been found for the master problem, but there are some open subproblems:")
            print("Therefor, the final heurstic is called to make a feasible solution")
            Number_of_Problamatic_Nodes=len(Problamatic_Nodes)
            print("The size of problamatic nodes and their values: ")
            print(Number_of_Problamatic_Nodes)
            print(Problematic_Values)
            print("Extra time dedicated for retreaving feasibilty", Time_for_Making_Final_Feasible_Solution)
            Time_for_Making_Final_Feasible_Solution= Time_for_Making_Final_Feasible_Solution/Number_of_Problamatic_Nodes/m
            print("Extra time dedicated for retreaving feasibilty of each probematic case per AGV", Time_for_Making_Final_Feasible_Solution)

            Values_of_Problamatic_Nodes_After_Retreaving_Feasibility=[]
            for index in range(Number_of_Problamatic_Nodes):
                start = timeit.default_timer()              
                Generated_feasible_Solution=Make_Feasible_Solution (num_jobs,num_b0,num_b1,num_b2,m,d,e,Time_for_Making_Final_Feasible_Solution,Problamatic_Nodes[index],Number_of_Thread,b,t)
                stop = timeit.default_timer()
                print("Spent time for problematic incumbent node ", index, "is ", (stop-start) )
                Spent_Time_on_Final_Heuristic=Spent_Time_on_Final_Heuristic+(stop-start)
                print("The overall time spent in retreaving the problematic cases is")
                print(Spent_Time_on_Final_Heuristic)
                print("And feasible value of this problamatic node is ")
                print(Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])
                Values_of_Problamatic_Nodes_After_Retreaving_Feasibility.append(Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])
                if (Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])<UB:
                    UB=Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m]
                    Optimal_Schedule=Problamatic_Nodes[index]
                    If_UB_From_Open_Problems_Is_Reported=1
                    If_Initial_UB_Is_Reported=0
                print("Values of all problamatic nodes after being feasible: ")
                print(Values_of_Problamatic_Nodes_After_Retreaving_Feasibility)
                print("The best found UB is")
                print(UB) 
                print("The best found LB is")
                print(LB)                
                Gap = (UB-LB)/UB          
                print("The overal spent time for this instance including the final heuristic")
                print(Running_Time,"+",Spent_Time_on_Final_Heuristic,"=",Running_Time+Spent_Time_on_Final_Heuristic)
            
        
        elif len(Last_Feasible_Node)>0 and Number_of_Cases_FCF_Exits_Because_of_Timelimit==0:
                Optimal_Schedule=cpx.solution.get_values()
                LB = cpx.solution.MIP.get_best_objective()
                UB = cpx.solution.get_objective_value()
                Gap = cpx.solution.MIP.get_mip_relative_gap()
                If_Initial_UB_Is_Reported=0
                print("The algorithm exits normally with found feasible (or optimal) solutions from algorithm.")

        elif len(Last_Feasible_Node)>0 and Number_of_Cases_FCF_Exits_Because_of_Timelimit>0:
                Optimal_Schedule=cpx.solution.get_values()
                LB = cpx.solution.MIP.get_best_objective()
                UB = cpx.solution.get_objective_value()
                Gap = cpx.solution.MIP.get_mip_relative_gap()
                If_Initial_UB_Is_Reported=0
                print("The algorithm finds some feasible nodes, also there are some open subproblems")
                if LB!=UB and Time_for_Making_Final_Feasible_Solution>0:
                    Number_of_Problamatic_Nodes=len(Problamatic_Nodes)
                    print("The size of problamatic nodes and their values: ")
                    print(Number_of_Problamatic_Nodes)
                    print(Problematic_Values)
                    print("Extra time dedicated for retreaving feasibilty", Time_for_Making_Final_Feasible_Solution)
                    Time_for_Making_Final_Feasible_Solution= Time_for_Making_Final_Feasible_Solution/Number_of_Problamatic_Nodes/m
                    print("Extra time dedicated for retreaving feasibilty of each probematic case per AGV", Time_for_Making_Final_Feasible_Solution)

                    Values_of_Problamatic_Nodes_After_Retreaving_Feasibility=[]
                    for index in range(Number_of_Problamatic_Nodes):
                        start = timeit.default_timer()              
                        Generated_feasible_Solution=Make_Feasible_Solution (num_jobs,num_b0,num_b1,num_b2,m,d,e,Time_for_Making_Final_Feasible_Solution,Problamatic_Nodes[index],Number_of_Thread,b,t)
                        stop = timeit.default_timer()
                        print("Spent time for problematic incumbent node ", index, "is ", (stop-start) )
                        Spent_Time_on_Final_Heuristic=Spent_Time_on_Final_Heuristic+(stop-start)
                        print("The overall time spent in retreaving the problematic cases is")
                        print(Spent_Time_on_Final_Heuristic)
                        print("And feasible value of this problamatic node is ")
                        print(Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])
                        Values_of_Problamatic_Nodes_After_Retreaving_Feasibility.append(Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])
                        UB=Given_UB
                        if (Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])<UB:
                            UB=Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m]
                            Optimal_Schedule=Problamatic_Nodes[index]
                            If_UB_From_Open_Problems_Is_Reported=1
                        print("Values of all problamatic nodes after being feasible: ")
                        print(Values_of_Problamatic_Nodes_After_Retreaving_Feasibility)
                        print("The best found UB is")
                        print(UB) 
                        print("The best found LB is")
                        print(LB)                
                        Gap = (UB-LB)/UB          
                        print("The overal spent time for this instance including the final heuristic")
                        print(Running_Time,"+",Spent_Time_on_Final_Heuristic,"=",Running_Time+Spent_Time_on_Final_Heuristic)

        return [LB,UB,Gap,Running_Time,Optimal_Schedule,cpx.solution.get_status(),cpx.solution.progress.get_num_nodes_processed(),cpx.solution.MIP.get_num_cuts(cpx.solution.MIP.cut_type.user),Number_of_Feasibilty_Cut,Number_of_Combinatorial_Cut,Number_of_Iteration,Number_of_CBPP2_Check_Recalled,Number_of_Feasibility_Check_Recalled,If_LBBD_Exits_With_No_Found_Feasible_Solution,Number_of_Cases_FCF_Exits_Because_of_Timelimit,Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit,Elapsed_Time_on_Feasiblity_Check,Elapsed_Time_on_Cuts,If_LBBD_Exits_With_No_Found_Node,Spent_Time_on_Final_Heuristic,If_Initial_UB_Is_Reported,If_UB_From_Open_Problems_Is_Reported]

    except cplex.exceptions.CplexSolverError as exp:
        print(f"CPLEX Solver Error: {exp}")  # Print the error message
        try: 
            If_LBBD_Exits_With_No_Found_Feasible_Solution=1            
            print("No feasible solution is found by the algorithm (all nodes have been rejected) ")
            if Number_of_Cases_FCF_Exits_Because_of_Timelimit>0 and Time_for_Making_Final_Feasible_Solution>0:  
                print("But some open subproblems exist")
                Number_of_Problamatic_Nodes=len(Problamatic_Nodes)
                print("The size of problamatic nodes and their values: ")
                print(Number_of_Problamatic_Nodes)
                print(Problematic_Values)
                print("Extra time dedicated for retreaving feasibilty", Time_for_Making_Final_Feasible_Solution)
                Time_for_Making_Final_Feasible_Solution= Time_for_Making_Final_Feasible_Solution/Number_of_Problamatic_Nodes/m
                print("Extra time dedicated for retreaving feasibilty of each probematic case per AGV", Time_for_Making_Final_Feasible_Solution)

                Values_of_Problamatic_Nodes_After_Retreaving_Feasibility=[]
                for index in range(Number_of_Problamatic_Nodes):
                    start = timeit.default_timer()              
                    Generated_feasible_Solution=Make_Feasible_Solution (num_jobs,num_b0,num_b1,num_b2,m,d,e,Time_for_Making_Final_Feasible_Solution,Problamatic_Nodes[index],Number_of_Thread,b,t)
                    stop = timeit.default_timer()
                    print("Spent time for problematic incumbent node ", index, "is ", (stop-start) )
                    Spent_Time_on_Final_Heuristic=Spent_Time_on_Final_Heuristic+(stop-start)
                    print("The overall time spent in retreaving the problematic cases is")
                    print(Spent_Time_on_Final_Heuristic)
                    print("And feasible value of this problamatic node is ")
                    print(Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])
                    Values_of_Problamatic_Nodes_After_Retreaving_Feasibility.append(Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])
                    if (Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m])<UB:
                        UB=Generated_feasible_Solution[(num_jobs+num_b0+num_b1+num_b2)*m+m]
                        Optimal_Schedule=Problamatic_Nodes[index]
                        If_UB_From_Open_Problems_Is_Reported=1
                        If_Initial_UB_Is_Reported=0
                    print("Values of all problamatic nodes after being feasible: ")
                    print(Values_of_Problamatic_Nodes_After_Retreaving_Feasibility)
                    print("The best found UB is")
                    print(UB) 
                    print("The best found LB is")
                    print(LB)                
                    Gap = (UB-LB)/UB          
                    print("The overal spent time for this instance including the final heuristic")
                    print(Running_Time,"+",Spent_Time_on_Final_Heuristic,"=",Running_Time+Spent_Time_on_Final_Heuristic)

            return [LB,UB,Gap,Running_Time,Optimal_Schedule,cpx.solution.get_status(),cpx.solution.progress.get_num_nodes_processed(),cpx.solution.MIP.get_num_cuts(cpx.solution.MIP.cut_type.user),Number_of_Feasibilty_Cut,Number_of_Combinatorial_Cut,Number_of_Iteration,Number_of_CBPP2_Check_Recalled,Number_of_Feasibility_Check_Recalled,If_LBBD_Exits_With_No_Found_Feasible_Solution,Number_of_Cases_FCF_Exits_Because_of_Timelimit,Number_of_Cases_FCF_of_MIS_Exits_Because_of_Timelimit,Elapsed_Time_on_Feasiblity_Check,Elapsed_Time_on_Cuts,If_LBBD_Exits_With_No_Found_Node,Spent_Time_on_Final_Heuristic,If_Initial_UB_Is_Reported,If_UB_From_Open_Problems_Is_Reported]

        except Exception as exp:
            print(f"Error retrieving information about the last found nodeeeeeeeeeeeeeeeeeeeeeeeee: {exp}")