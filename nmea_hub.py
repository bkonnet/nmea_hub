#!/usr/bin/env python3
import asyncio

# ==== Config por defecto ===
UDP_PORT = 20010   # Puerto de entrada UDP
TCP_PORT = 10110   # Puerto de salida TCP

clients = set()

def normalize(nmea_bytes: bytes) -> list[bytes]:
    """Elimina bytes nulos y asegura terminadores \r\n por sentencia."""
    if not nmea_bytes:
        return []
    data = (nmea_bytes
            .replace(b'\x00', b'')
            .replace(b'\r\n', b'\n')
            .replace(b'\r', b'\n'))
    lines = [l for l in data.split(b'\n') if l.strip()]
    return [l.rstrip() + b'\r\n' for l in lines]

class UdpProto(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr):
        sentences = normalize(data)
        if not sentences:
            return
        dead = []
        for w in clients:
            try:
                for s in sentences:
                    w.write(s)
            except Exception:
                dead.append(w)
        for d in dead:
            clients.discard(d)

async def tcp_handler(reader, writer):
    clients.add(writer)
    try:
        await reader.read()  # mantenemos la conexión hasta que el cliente cierre
    finally:
        clients.discard(writer)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def main():
    loop = asyncio.get_running_loop()
    # UDP receptor (escucha en todas las interfaces)
    await loop.create_datagram_endpoint(lambda: UdpProto(),
                                        local_addr=('0.0.0.0', UDP_PORT))
    # TCP servidor para consumidores (OpenCPN/otros)
    server = await asyncio.start_server(tcp_handler, '0.0.0.0', TCP_PORT)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"NMEA Hub: UDP:{UDP_PORT} -> TCP:{TCP_PORT} | Listening on {addrs}")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
