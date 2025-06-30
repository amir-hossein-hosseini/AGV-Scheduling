def Extract_Data_for_Selected_Jobs(List_of_Assigned_Jobs_to_This_AGV, n, d,e):
    
    List_of_Jobs = []
    List_of_Bins = []
    for j in range(len(List_of_Assigned_Jobs_to_This_AGV)):
        if List_of_Assigned_Jobs_to_This_AGV[j] <= n and List_of_Assigned_Jobs_to_This_AGV[j] > 0:
            List_of_Jobs.append(int(List_of_Assigned_Jobs_to_This_AGV[j]))
        elif List_of_Assigned_Jobs_to_This_AGV[j] > n and List_of_Assigned_Jobs_to_This_AGV[j] > 0:
            List_of_Bins.append(int(List_of_Assigned_Jobs_to_This_AGV[j]))
    
    
    
    param_dict = {}
    # Assign parameters to elements in e
    for i in range(len(e)):
        param_dict[i] = e[i]

    e_of_Selected_Jobs = []
    for elem in List_of_Jobs:
            e_of_Selected_Jobs.append(param_dict.get(elem-1,0))

    param_dict = {}
    # Assign parameters to elements in e
    for i in range(len(d)):
        param_dict[i] = d[i]

    d_of_Selected_Jobs = []
    for elem in List_of_Jobs:
            d_of_Selected_Jobs.append(param_dict.get(elem-1,0))
    
    return [List_of_Jobs,List_of_Bins,d_of_Selected_Jobs, e_of_Selected_Jobs]