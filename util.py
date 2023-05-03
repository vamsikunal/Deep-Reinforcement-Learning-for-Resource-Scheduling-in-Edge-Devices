import numpy as np

mob = np.zeros((60, 2))
f1 = [(3,4),(6,3)]
loc = np.zeros((1, 2))

now_sec = 0
for line in f1:
    for sec in range(30):
        mob[now_sec + sec][0] = line[0]  # x
        mob[now_sec + sec][1] = line[1]  # y
    now_sec += 30
loc[0] = mob[0]


print(mob)