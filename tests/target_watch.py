from threading import Thread
from time import sleep


def say(word="default"):
    print(word)


def target():
    for _ in range(15):
        say()
        sleep(0.2)


thread = Thread(target=target)
thread.start()
thread.join()
