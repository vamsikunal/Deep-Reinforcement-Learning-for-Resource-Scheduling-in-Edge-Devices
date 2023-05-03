import random
import numpy as np
import math
import matplotlib.pyplot as plt


LOCATION = "KAIST"
USER_NUM = 25
EDGE_NUM = 20
LIMIT = 4
MAX_EP_STEPS = 3000
TXT_NUM = 92
r_bound = 1e9 * 0.063
b_bound = 1e9

#####################  function  ####################
# Shannon-Hartley theorem
def trans_rate(user_loc, edge_loc):
    B = 2e6
    P = 0.25
    d = np.sqrt(np.sum(np.square(user_loc[0] - edge_loc))) + 0.01
    h = 4.11 * math.pow(3e8 / (4 * math.pi * 915e6 * d), 2) #Channel gain
    N = 1e-10 #Noise power
    return B * math.log2(1 + P * h / N)

# Lower-triangular matrices
def BandwidthTable(edge_num):
    BandwidthTable = np.zeros((edge_num, edge_num))
    for i in range(0, edge_num):
        for j in range(i+1, edge_num):
                BandwidthTable[i][j] = 1e9
    return BandwidthTable 

def two_to_one(two_table):
    one_table = two_table.flatten()
    return one_table

def generate_state(two_table, U, E, x_min, y_min):
    # initial
    one_table = two_to_one(two_table)
    S = np.zeros((len(E) + one_table.size + len(U) + len(U)*2))
    # transform
    count = 0
    # available resource of each edge server
    for edge in E:
        S[count] = edge.capability/(r_bound*10)
        count += 1
    # available bandwidth of each connection
    for i in range(len(one_table)):
        S[count] = one_table[i]/(b_bound*10)
        count += 1
    # offloading of each user
    for user in U:
        S[count] = user.req.edge_id/100
        count += 1
    # location of the user
    for user in U:
        S[count] = (user.loc[0][0] + abs(x_min))/1e5
        S[count+1] = (user.loc[0][1] + abs(y_min))/1e5
        count += 2
    return S

def generate_action(R, B, O):
    # resource
    a = np.zeros(USER_NUM + USER_NUM + EDGE_NUM * USER_NUM)
    a[:USER_NUM] = R / r_bound
    # bandwidth
    a[USER_NUM:USER_NUM + USER_NUM] = B / b_bound
    # offload
    base = USER_NUM + USER_NUM
    for user_id in range(USER_NUM):
        a[base + int(O[user_id])] = 1
        base += EDGE_NUM
    return a

def get_minimum():
    cal = np.zeros((1, 2))
    for data_num in range(TXT_NUM):
        data_name = str("%03d" % (data_num + 1))  # plus zero
        file_name = LOCATION + "_30sec_" + data_name + ".txt"
        file_path = "data/" + LOCATION + "/" + file_name
        f = open(file_path, "r")
        f1 = f.readlines()
        # get line_num
        line_num = 0
        for line in f1:
            line_num += 1
        # collect the data from the .txt
        data = np.zeros((line_num, 2))
        index = 0
        for line in f1:
            data[index][0] = line.split()[1]  # x
            data[index][1] = line.split()[2]  # y
            index += 1
        # put data into the cal
        cal = np.vstack((cal, data))
    return min(cal[:, 0]), min(cal[:, 1])

# Edge device will be present at each group mean location
def proper_edge_loc(edge_num):

    # initial the e_l
    e_l = np.zeros((edge_num, 2))
    # calculate the mean of the data
    group_num = math.floor(TXT_NUM / edge_num)
    edge_id = 0
    for base in range(0, group_num*edge_num, group_num):
        for data_num in range(base, base + group_num):
            data_name = str("%03d" % (data_num + 1))  # plus zero
            file_name = LOCATION + "_30sec_" + data_name + ".txt"
            file_path = "data/" + LOCATION + "/" + file_name
            f = open(file_path, "r")
            f1 = f.readlines()
            # get line_num and initial data
            line_num = 0
            for line in f1:
                line_num += 1
            data = np.zeros((line_num, 2))
            # collect the data from the .txt
            index = 0
            for line in f1:
                data[index][0] = line.split()[1]  # x
                data[index][1] = line.split()[2]  # y
                index += 1
            # stack the collected data
            if data_num % group_num == 0:
                cal = data
            else:
                cal = np.vstack((cal, data))
        e_l[edge_id] = np.mean(cal, axis=0)
        edge_id += 1
    return e_l

#############################UE###########################

# Class is used to simulate the mobility of a user
class UE():
    def __init__(self, user_id, data_num):
        self.user_id = user_id  # number of the user
        self.loc = np.zeros((1, 2))
        self.num_step = 0  # the number of step

        # calculate num_step and define self.mob
        data_num = str("%03d" % (data_num + 1))  # plus zero
        file_name = LOCATION + "_30sec_" + data_num + ".txt"
        file_path = "data/" + LOCATION + "/" + file_name
        f = open(file_path, "r")
        f1 = f.readlines()
        data = 0
        for line in f1:
            data += 1
        self.num_step = data * 30
        self.mob = np.zeros((self.num_step, 2))

        # write data to self.mob
        now_sec = 0
        for line in f1:
            for sec in range(30):
                self.mob[now_sec + sec][0] = line.split()[1]  # x
                self.mob[now_sec + sec][1] = line.split()[2]  # y
            now_sec += 30
        self.loc[0] = self.mob[0]

    def generate_request(self, edge_id):
        self.req = Request(self.user_id, edge_id)

    def request_update(self):
        # default request.state == 5 means disconnection ,6 means migration
        if self.req.state == 5:
            self.req.timer += 1
        else:
            self.req.timer = 0
            if self.req.state == 0:
                self.req.state = 1
                self.req.u2e_size = self.req.tasktype.req_u2e_size
                self.req.u2e_size -= trans_rate(self.loc, self.req.edge_loc)
            elif self.req.state == 1:
                if self.req.u2e_size > 0:
                    self.req.u2e_size -= trans_rate(self.loc, self.req.edge_loc)
                else:
                    self.req.state = 2
                    self.req.process_size = self.req.tasktype.process_loading
                    self.req.process_size -= self.req.resource
            elif self.req.state == 2:
                if self.req.process_size > 0:
                    self.req.process_size -= self.req.resource
                else:
                    self.req.state = 3
                    self.req.e2u_size = self.req.tasktype.req_e2u_size
                    self.req.e2u_size -= 10000  # value is small,so simplify
            else:
                if self.req.e2u_size > 0:
                    self.req.e2u_size -= 10000  # B*math.log(1+SINR(self.user.loc, self.offloading_serv.loc), 2)/(8*time_scale)
                else:
                    self.req.state = 4

    def mobility_update(self, time):  # t: second
        if time < len(self.mob[:, 0]):
            self.loc[0] = self.mob[time]   # x

        else:
            self.loc[0][0] = np.inf
            self.loc[0][1] = np.inf

class Request(): # (user_id, edge_id, edge_loc, state, u2e_size, process_size, e2u_size, resource, mig_size, tasktype, last_offlaoding, timer)
    def __init__(self, user_id, edge_id):
        # id
        self.user_id = user_id
        self.edge_id = edge_id
        self.edge_loc = 0
        # state
        self.state = 5     # 5: not connect
        self.pre_state=5
        # transmission size
        self.u2e_size = 0
        self.process_size = 0
        self.e2u_size = 0
        # edge state
        self.resource = 0
        self.mig_size = 0
        # tasktype
        self.tasktype = TaskType()
        self.last_offlaoding = 0
        # timer
        self.timer = 0

class TaskType():
    def __init__(self):
        ##Objection detection: VOC SSD300
        # transmission
        self.req_u2e_size = 300 * 300 * 3 * 1 #Image (300 x 300) and the number of color channels (3).
        self.process_loading = 300 * 300 * 3 * 4 #floating-point operations
        self.req_e2u_size = 4 * 4 + 20 * 4 #size of (output + metadata)
        # migration
        self.migration_size = 2e9
    def task_inf(self):
        return "req_u2e_size:" + str(self.req_u2e_size) + "\nprocess_loading:" + str(self.process_loading) + "\nreq_e2u_size:" + str(self.req_e2u_size)

#############################EdgeServer###################

class EdgeServer():
    def __init__(self, edge_id, loc):
        self.edge_id = edge_id  # edge server number
        self.loc = loc
        self.capability = 1e9 * 0.063
        self.user_group = []
        self.limit = LIMIT
        self.connection_num = 0
    def maintain_request(self, R, U):
        
        for user in U:
            # the number of the connection user
            self.connection_num = 0
            for user_id in self.user_group:
                if U[user_id].req.state != 6:
                    self.connection_num += 1
            # maintain the request
            if user.req.edge_id == self.edge_id and self.capability - R[user.user_id] > 0:
                # maintain the preliminary connection
                if user.req.user_id not in self.user_group and self.connection_num+1 <= self.limit:
                    # first time : do not belong to any edge(user_group)
                    self.user_group.append(user.user_id)  # add to the user_group
                    user.req.state = 0  # prepare to connect
                    # notify the request
                    user.req.edge_id = self.edge_id
                    user.req.edge_loc = self.loc

                # dispatch the resource
                user.req.resource = R[user.user_id]
                self.capability -= R[user.user_id]

    def migration_update(self, O, B, table, U, E):

        # maintain the the migration
        for user_id in self.user_group:
            # prepare to migration
            if U[user_id].req.edge_id != O[user_id]:
                # initial
                ini_edge = int(U[user_id].req.edge_id)
                target_edge = int(O[user_id])
                if table[ini_edge][target_edge] - B[user_id] >= 0:
                    # on the way to migration, but offloading to another edge computer(step 1)
                    if U[user_id].req.state == 6 and target_edge != U[user_id].req.last_offlaoding:
                        # reduce the bandwidth
                        table[ini_edge][target_edge] -= B[user_id]
                        # start migration
                        U[user_id].req.mig_size = U[user_id].req.tasktype.migration_size
                        U[user_id].req.mig_size -= B[user_id]
                        #print("user", U[user_id].req.user_id, ":migration step 1")
                    # first try to migration(step 1)
                    elif U[user_id].req.state != 6:
                        table[ini_edge][target_edge] -= B[user_id]
                        # start migration
                        U[user_id].req.mig_size = U[user_id].req.tasktype.migration_size
                        U[user_id].req.mig_size -= B[user_id]
                        # store the pre state
                        U[user_id].req.pre_state = U[user_id].req.state
                        # on the way to migration, disconnect to the old edge
                        U[user_id].req.state = 6
                        #print("user", U[user_id].req.user_id, ":migration step 1")
                    elif U[user_id].req.state == 6 and target_edge == U[user_id].req.last_offlaoding:
                        # keep migration(step 2)
                        if U[user_id].req.mig_size > 0:
                            # reduce the bandwidth
                            table[ini_edge][target_edge] -= B[user_id]
                            U[user_id].req.mig_size -= B[user_id]
                            #print("user", U[user_id].req.user_id, ":migration step 2")
                        # end the migration(step 3)
                        else:
                            # the number of the connection user
                            target_connection_num = 0
                            for target_user_id in E[target_edge].user_group:
                                if U[target_user_id].req.state != 6:
                                    target_connection_num += 1
                            #print("user", U[user_id].req.user_id, ":migration step 3")
                            # change to another edge
                            if E[target_edge].capability - U[user_id].req.resource >= 0 and target_connection_num + 1 <= E[target_edge].limit:
                                # register in the new edge
                                E[target_edge].capability -= U[user_id].req.resource
                                E[target_edge].user_group.append(user_id)
                                self.user_group.remove(user_id)
                                # update the request
                                # id
                                U[user_id].req.edge_id = E[target_edge].edge_id
                                U[user_id].req.edge_loc = E[target_edge].loc
                                # release the pre-state, continue to transmission process
                                U[user_id].req.state = U[user_id].req.pre_state
                                #print("user", U[user_id].req.user_id, ":migration finish")
            #store pre_offloading
            U[user_id].req.last_offlaoding = int(O[user_id])

        return table

    #release the all resource
    def release(self):
        self.capability = 1e9 * 0.063


#############################Env###########################

class Env():
    def __init__(self):
        self.step = 30
        self.time = 0
        self.edge_num = EDGE_NUM  # the number of servers
        self.user_num = USER_NUM  # the number of users
        # define environment object
        self.reward_all = []
        self.U = []
        self.fin_req_count = 0
        self.prev_count = 0
        self.rewards = 0
        self.R = np.zeros((self.user_num))
        self.O = np.zeros((self.user_num))
        self.B = np.zeros((self.user_num))
        self.table = BandwidthTable(self.edge_num)
        self.priority = np.zeros((self.user_num, self.edge_num))
        self.E = []
        self.x_min, self.y_min = get_minimum()

        self.e_l = 0
        self.model = 0

    def get_inf(self):
        # s_dim
        self.reset()
        s = generate_state(self.table, self.U, self.E, self.x_min, self.y_min)
        s_dim = s.size

        # a_dim
        r_dim = len(self.U)
        b_dim = len(self.U)
        o_dim = self.edge_num * len(self.U)

        # maximum resource
        r_bound = self.E[0].capability

        # maximum bandwidth
        b_bound = self.table[0][1]
        b_bound = b_bound.astype(np.float32)

        # task size
        task = TaskType()
        task_inf = task.task_inf()

        return s_dim, r_dim, b_dim, o_dim, r_bound, b_bound, task_inf, LIMIT, LOCATION

    def reset(self):
        # reset time
        self.time = 0
        # reward
        self.reward_all = []
        # user
        self.U = []
        self.fin_req_count = 0
        self.prev_count = 0
        data_num = random.sample(list(range(TXT_NUM)), self.user_num)
        for i in range(self.user_num):
            new_user = UE(i, data_num[i])
            self.U.append(new_user)
        # Resource
        self.R = np.zeros((self.user_num))
        # Offlaoding
        self.O = np.zeros((self.user_num))
        # bandwidth
        self.B = np.zeros((self.user_num))
        # bandwidth table
        self.table = BandwidthTable(self.edge_num)
        # server
        self.E = []
        e_l = proper_edge_loc(self.edge_num)
        for i in range(self.edge_num):
            new_e = EdgeServer(i, e_l[i, :])
            self.E.append(new_e)
            """
            print("edge", new_e.edge_id, "'s loc:\n", new_e.loc)
        print("========================================================")
        """

    
        for user in self.U:
            user.generate_request(self.O[user.user_id])
        return generate_state(self.table, self.U, self.E, self.x_min, self.y_min)

    def ddpg_step_forward(self, a, r_dim, b_dim):
        # release the bandwidth
        self.table = BandwidthTable(self.edge_num)
        # release the resource
        for edge in self.E:
            edge.release()

        # update the policy every second
        # resource update
        self.R = a[:r_dim]
        # bandwidth update
        self.B = a[r_dim:r_dim + b_dim]
        # offloading update
        base = r_dim + b_dim
        for user_id in range(self.user_num):
            prob_weights = a[base:base + self.edge_num]
            #print("user", user_id, ":", prob_weights)
            action = np.random.choice(range(len(prob_weights)), p=prob_weights.ravel())  # select action w.r.t the actions prob
            base += self.edge_num
            self.O[user_id] = action


        # request update
        for user in self.U:
            # update the state of the request
            user.request_update()
            if user.req.timer >= 5:
                user.generate_request(self.O[user.user_id])  # offload according to the priority
            # it has already finished the request
            if user.req.state == 4:
                # rewards
                self.fin_req_count += 1
                user.req.state = 5  # request turn to "disconnect"
                self.E[int(user.req.edge_id)].user_group.remove(user.req.user_id)
                user.generate_request(self.O[user.user_id])  # offload according to the priority

        # edge update
        for edge in self.E:
            edge.maintain_request(self.R, self.U)
            self.table = edge.migration_update(self.O, self.B, self.table, self.U, self.E)

        # rewards
        self.rewards = self.fin_req_count - self.prev_count
        self.prev_count = self.fin_req_count

        # every user start to move
        if self.time % self.step == 0:
            for user in self.U:
                user.mobility_update(self.time)

        # update time
        self.time += 1

        # return s_, r
        return generate_state(self.table, self.U, self.E, self.x_min, self.y_min), self.rewards

    def text_render(self):
        # print("R:", self.R)
        # print("B:", self.B)
        # """
        # base = USER_NUM +USER_NUM
        # for user in range(len(self.U)):
        #     print("user", user, " offload probabilty:", a[base:base + self.edge_num])
        #     base += self.edge_num
        # """
        # print("O:", self.O)
        # for user in self.U:
        #     print("user", user.user_id, "'s loc:\n", user.loc)
        #     print("request state:", user.req.state)
        #     print("edge serve:", user.req.edge_id)
        # for edge in self.E:
        #     print("edge", edge.edge_id, "user_group:", edge.user_group)
        # print("reward:", self.rewards)
        # print("=====================update==============================")
        pass

