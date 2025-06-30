import random


# Function to generate random list of D
def generate_D(n):
    return [random.randint(1, 100) for _ in range(n)]


# Parameters
n_values = [50, 100, 150, 200]
n_values = [50]
m_values = [5, 10]
m_values = [5]
T = 100
t_values = [T / 2, 2*T]
T = 100
t_values = [T / 2]
ins_num = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
ins_num = [1]
directory =r"C:\Users\amir_\Desktop\Test on LBBD"


for n in n_values:
        for m in m_values:
            for t in t_values:
                 for i in ins_num:


# Save instances to text file
                    with open(f"AAAAAAIns_V{m}_J{n}_T{int(t)}_{i}.txt", "w") as file:
                        D = generate_D(n)
                        file.write(f"m:{m}\tn:{n}\tt:{t}\tT:{T}\n")
                        file.write("D:[\n")
                        for d in D:
                            file.write(f"{d}\n")
                        file.write("]\n")
                        file.write("\n")
 

d = []
text = open(f"AAAAAAIns_V{m}_J{n}_T{int(t)}_{i}.txt", "r")
for i, line in enumerate(text):
    if i >= 2 and i <= n + 1:
        a = line.strip()
        d.append(int(a))
text.close()
print(d)