# return acceleration or quarternion data without none
def data_none(data):
    # if the leftmost data has none in them 
    if None in data[0]:
        #replace the value with the next not none value
        for i in range(len(data[0])):
            if data[0][i] == None:
                index = next_not_none(data, 0, i)
                if index == None:
                    error = "all values at axis %d is none" % i
                    return error
                data[0][i] = data[index][i]
    
    # if the rightmost data has none in them
    if None in data[len(data)-1]:
        # replace the rightmost data with not none value
        for i in range(len(data[len(data)-1])):
            if data[len(data)-1][i] == None:
                index = prev_not_none(data, len(data)-1, i)
                if index == None:
                    error = "all values at axis %d is none" % i
                    return error
                data[len(data)-1][i] = data[index][i]

    # for any none values in between, average for acc, or replace with the left for quaternion
    for i in range(1, len(data)-1):
        if None in data[i] and len(data[i]) == 3:
            # replace the none with the average of previous and next element
            for axis in range(len(data[i])):
                if data[i][axis] == None:
                    prev = prev_not_none(data, i, axis)
                    next = next_not_none(data, i, axis)
                    if prev == None or next == None:
                        error = "all values at axis %d is none" % i
                        return error
                    # average = (data[prev][axis] + data[next][axis])/2
                    data[i][axis] = (data[prev][axis] + data[next][axis])/2
        if None in data[i] and len(data[i]) == 4:
            # replace the none with the first not none value to the left for the quaternion
            for axis in range(len(data[i])):
                if data[i][axis] == None:
                    prev = prev_not_none(data, i, axis)
                    if prev == None:
                        error = "all values at axis %d is none" % i
                        return error
                    data[i][axis] = data[prev][axis]
    return data

# return the index of first not none value after the input index at the given axis
# return None if all values after the index is None
def next_not_none(data, index, axis):
    for i in range(index+1, len(data)):
        if data[i][axis] != None:
            return i
    return None

# return the index of first not none value before the input index at the given axis
# return None if all values after the index is None
def prev_not_none(data, index, axis):
    for i in range(index-1, -1, -1):
        if data[i][axis] != None:
            return i
    return None
    
# return a list of averaged acceleration, assuming input data has no None values
def average_acc(acc_data):
    # initialize averaged acceleration data
    averaged = [[0]*len(acc_data[0])]*len(acc_data)
    # averaged = [[0] * len(acc_data) for _ in range(acc_data[0])]
    averaged[0] = acc_data[0]
    averaged[len(averaged)-1] = acc_data[len(averaged)-1]
    for i in range(1, len(acc_data)-1):
        for axis in range(len(acc_data[i])):
            averaged[i][axis] = (acc_data[i-1][axis]+acc_data[i+1][axis])/2
    return averaged

# for testing purposes 

"""
data = [[1, 23, 51], [None, 41, 52], [None, 2, None]]
data1 = [[38, 7, 1, 30], 
        [None, None, None, 1], 
        [None, 2, None, 1],  
        [None, 4, 4, 1], 
        [8, 3, 9, 4]]
data2 = [[1, 23, 51], 
        [None, 41, 52], 
        [None, 2, None], 
        [2, 4, 1]]
print('prior to treatment')
print(data2)
treated = data_none(data2)
print('after getting rid of none')
print(data2)
average = average_acc(data2)
print("here's the output")
print(average)
"""