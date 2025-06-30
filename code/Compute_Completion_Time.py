# Function: Computing completion time of an AGV for a given solution

def Compute_Completion_Time (s,d,e,num_jobs,num_b0, t=60,b=10):
    Completion_Time=0

    for l in range(int(len(s))):
        j=int(s[l])

        if j>0:
            if  j <= num_jobs:
                Completion_Time=d[j-1]+Completion_Time
            elif j > num_jobs+num_b0:
                Completion_Time=Completion_Time+t
        else:
            break
    
    
    return Completion_Time