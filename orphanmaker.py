#!/usr/bin/python

import os
import time

pid = os.fork()

if pid == 0:
    pid = os.fork()
    if pid == 0:
        time.sleep(1)
        print("exiting the orphaned grand-child, turning it into a zombie")
        os._exit(0)
    else:
        time.sleep(0.5)
        print("exiting the child, turning grand-child into an orphan")
        os._exit(0)

else:
    print("running the 'server'... ^C to exit and clean everything up")
    while True:
        time.sleep(2)


