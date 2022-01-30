import time

INTV = 0.1
last_sample = time.monotonic()
print("hi")
while(True):
    this_sample = time.monotonic()
    if(this_sample - last_sample >= INTV):
        print(this_sample-last_sample)
        last_sample = this_sample
