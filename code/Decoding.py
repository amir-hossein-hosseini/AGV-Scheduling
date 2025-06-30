
# Function: Decoding an (1D) array of the solution to the agv scheduling 

def Decoding (m, num_jobs,num_b0,num_b1,num_b2, candidate_point):
    import numpy as np
          
    Number_of_assigned_jobs=[0]*m
    for i in range(m):
        for j in range(num_jobs+num_b0+num_b1+num_b2):
                if candidate_point[j*m+i] >0:
                    Number_of_assigned_jobs[i]=Number_of_assigned_jobs[i]+1
                    

    AJ = np.zeros((m,max(Number_of_assigned_jobs)))
    for i in range(m):
        l=0
        Assigned_jobs=[None]* Number_of_assigned_jobs[i]
        for j in range(num_jobs+num_b0+num_b1+num_b2):
                if candidate_point[j*m+i] >0:
                    Assigned_jobs[l]=j+1
                    AJ[i,l]=j+1
                    l=l+1
                
     #   print("Assinged jobs to machine",f"{i}=", Assigned_jobs)  
    #    print(AJ)
    
    return [Number_of_assigned_jobs,AJ]