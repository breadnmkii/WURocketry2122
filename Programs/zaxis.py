# input: a list of altimeter reading
# output: a list of z acceleration reading from the frame of altimeter
def find_acc(z_dist, interval):
    acc = [None]*len(z_dist)
    acc[0] = 0
    acc[1] = 0
    for i in range(2, len(z_dist)):
        prev_velocity = (z_dist[i-1]-z_dist[i-2])/interval
        # print(z_dist[i-2])
        next_velocity = (z_dist[i]-z_dist[i-1])/interval
        print(prev_velocity)
        acc[i] = (next_velocity-prev_velocity)/interval
    return acc

# testing set 
'''
z = [0.000005763641, 11.00539, 19.26218,27.52266,33.02851,46.8004,55.06755]
interval = 0.05
acc = find_acc(z, interval)
print(acc)
'''