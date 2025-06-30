# Function: Extractinga a feasible solution from a given one
import numpy as np
from Extract_Data_for_Selected_Jobs import *
from Decoding import *
from BPP import *

def Make_Feasible_Solution (n,b0,b1,b2,m,d,e,Time,Variables_Values,Number_of_Thread,BC=10,CT=60):

    [Number_of_assigned_jobs, Matrix_of_Jobs_on_AGVs] = Decoding(m,n,b0,b1,b2,Variables_Values,)
    The_Last_Used_Bin=np.max(Matrix_of_Jobs_on_AGVs.flatten())
    for AGV in range(m):
        List_of_Assigned_Jobs_to_This_AGV=Matrix_of_Jobs_on_AGVs[AGV][:]

        [List_of_Jobs,List_of_Bins,d_of_Selected_Jobs, e_of_Selected_Jobs]=Extract_Data_for_Selected_Jobs(List_of_Assigned_Jobs_to_This_AGV,n, d, e)

        [LB_on_Needed_Bins, UB_on_Needed_Bins, X, Gap_of_BPP, Running_Time_BPP]=BPP(len(List_of_Jobs),e_of_Selected_Jobs,Time,Number_of_Thread,BC)

        if UB_on_Needed_Bins<=len(List_of_Bins):
            is_feasible=True
            print(f"AGV{AGV+1} is feasible")
        elif LB_on_Needed_Bins> len(List_of_Bins):
            is_feasible=False
            print(f"AGV{AGV+1} is not feasible")
            New_Bins=UB_on_Needed_Bins-len(List_of_Bins)
            print("number of new opened bins",New_Bins)
            for j in range(int(New_Bins)):
                The_Last_Used_Bin=The_Last_Used_Bin+1
                Variables_Values[(int(The_Last_Used_Bin)-1)*m+AGV]=1.0
                Completion_Time=  sum(d_of_Selected_Jobs)+(len(List_of_Bins)+int(New_Bins)-1)*CT
                print("Completion time of this AGV:",Completion_Time)
                Variables_Values[(n+b0+b1+b2)*m+AGV]=Completion_Time
        else:
            is_feasible=None
            print(f"AGV{AGV+1} is not clear")
            New_Bins=UB_on_Needed_Bins-len(List_of_Bins)
            print("number of new opened bins",New_Bins)
            for j in range(int(New_Bins)):
                The_Last_Used_Bin=The_Last_Used_Bin+1
                Variables_Values[(int(The_Last_Used_Bin)-1)*m+AGV]=1.0
                Completion_Time=  sum(d_of_Selected_Jobs)+(len(List_of_Bins)+int(New_Bins)-1)*CT
                print("Completion time of this AGV:",Completion_Time)
                Variables_Values[(n+b0+b1+b2)*m+AGV]=Completion_Time
      
    Variables_Values[(n+b0+b1+b2)*m+m]=max(Variables_Values[(n+b0+b1+b2)*m:(n+b0+b1+b2)*m+m])


    return Variables_Values