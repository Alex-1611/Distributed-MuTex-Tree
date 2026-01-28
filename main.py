import asyncio
import random
import sys

PORT = None
using = False
holder = None
request_queue = None
asked = False
connections = {}
token_received = None


async def send_message(target_port, message):
    global connections
    try:
        if target_port not in connections:
            reader, writer = await asyncio.open_connection('127.0.0.1', target_port)
            connections[target_port] = (reader, writer)
        else:
            reader, writer = connections[target_port]

        writer.write(f"{message}\n".encode())
        await writer.drain()
        print(f"[Node {PORT}] Sent to {target_port}: {message}")
    except Exception as e:
        print(f"[Node {PORT}] Error sending to {target_port}: {e}")
        if target_port in connections:
            del connections[target_port]


async def assign_privilege():
    global holder, using

    if holder == PORT and not request_queue.empty() and not using:
        first = request_queue.get_nowait()
        if first == PORT:
            using = True
            token_received.set()
        else:
            holder = first
            await send_message(first, f"TOKEN {PORT}")
            print(f"[Node {PORT}] Passed token to {first}")


async def make_request():
    global asked

    if holder != PORT and not request_queue.empty() and not asked:
        asked = True
        await send_message(holder, f"REQUEST {PORT}")
        print(f"[Node {PORT}] Sent REQUEST toward {holder}")


async def request_cs():
    await request_queue.put(PORT)
    print(f"[Node {PORT}] Added self to queue")
    await assign_privilege()
    await make_request()


async def release_cs():
    global using
    using = False
    await assign_privilege()
    await make_request()


async def handle_message(message):
    global holder, asked

    parts = message.split()
    command = parts[0]
    sender_port = int(parts[1])

    print(f"[Node {PORT}] Received from {sender_port}: {command}")

    if command == "REQUEST":
        await request_queue.put(sender_port)
        await assign_privilege()
        await make_request()
    elif command == "TOKEN":
        holder = PORT
        asked = False
        await assign_privilege()
        await make_request()


async def receive_messages(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[Node {PORT}] Connection from {addr}")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            message = data.decode().strip()
            if message:
                await handle_message(message)
    except Exception as e:
        print(f"[Node {PORT}] Connection error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def accept_connections():
    server = await asyncio.start_server(receive_messages, '127.0.0.1', PORT)
    print(f"[Node {PORT}] Server listening on 127.0.0.1:{PORT}")
    async with server:
        await server.serve_forever()


async def working_section():
    await asyncio.sleep(2)

    while True:
        await asyncio.sleep(random.uniform(1.5, 2.5))

        if random.random() < 0.33:
            print(f"[Node {PORT}] Wants to enter critical section")

            token_received.clear()
            await request_cs()
            await token_received.wait()

            print(f"\033[31m[Node {PORT}] *** ENTERING CRITICAL SECTION ***\033[0m")
            await asyncio.sleep(3)
            print(f"\033[32m[Node {PORT}] *** LEAVING CRITICAL SECTION ***\033[0m")

            await release_cs()


async def main():
    global PORT, holder, token_received, request_queue
    if len(sys.argv) < 3:
        print("Usage: python main.py <self_port> <holder_port>")
        sys.exit(1)

    PORT = int(sys.argv[1])
    holder = int(sys.argv[2])
    token_received = asyncio.Event()
    request_queue = asyncio.Queue()

    if holder == PORT:
        print(f"[Node {PORT}] Starting with TOKEN")
    else:
        print(f"[Node {PORT}] Starting, holder direction: {holder}")

    await asyncio.gather(
        accept_connections(),
        working_section()
    )

if __name__ == "__main__":
    asyncio.run(main())