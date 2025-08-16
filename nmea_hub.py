#!/usr/bin/env python3
import asyncio, re

UDP_PORT = 20010       # desde tu nodo local
TCP_PORT = 10110       # para tus OpenCPN remotos

clients = set()
line_end = re.compile(rb'\r?\n')

def normalize(nmea_bytes: bytes) -> list[bytes]:
    if not nmea_bytes:
        return []
    # homogeneiza saltos, elimina nulos, asegura \r\n por oración
    data = nmea_bytes.replace(b'\x00', b'').replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    lines = [l for l in data.split(b'\n') if l.strip()]
    return [l.rstrip() + b'\r\n' for l in lines]

class UdpProto(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr):
        for sentence in normalize(data):
            dead = []
            for w in clients:
                try:
                    w.write(sentence)
                except Exception:
                    dead.append(w)
            for d in dead:
                clients.discard(d)

async def tcp_handler(reader, writer):
    clients.add(writer)
    try:
        await reader.read()  # mantenemos la conexión abierta; no esperamos nada del cliente
    finally:
        clients.discard(writer)
        writer.close()
        await writer.wait_closed()

async def main():
    loop = asyncio.get_running_loop()
    # UDP receptor
    await loop.create_datagram_endpoint(lambda: UdpProto(),
                                        local_addr=('0.0.0.0', UDP_PORT))
    # TCP servidor para OpenCPN
    server = await asyncio.start_server(tcp_handler, '0.0.0.0', TCP_PORT)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
