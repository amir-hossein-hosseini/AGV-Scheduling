# The function which makes an array of the name of the variables
def generate_decision_variable_list(num_jobs, num_machines):
    variable_list = []
    for job in range(1, num_jobs + 1):
        for machine in range(1, num_machines + 1):
            variable_list.append(f'X_{job},{machine}')
    for machine in range(1, num_machines + 1):
        variable_list.append(f'C_{machine}')
    variable_list.append('C_Max')
    return variable_list