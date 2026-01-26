import asyncio
import queue
import sys


PORT = None
nodes = []
using = False
holder = None
request_queue = queue.Queue()
asked = False

def main():
    global PORT, nodes, holder
    PORT = sys.argv[1]
    if sys.argv[2] == 'self':
        holder = 0




if __name__ == "__main__":
    main()