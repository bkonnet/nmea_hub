# NMEA Hub (UDP → TCP Fan-out con Normalización)

Micro-hub en **Python 3** que:
- **Recibe NMEA por UDP** (desde uno o varios emisores).
- **Normaliza** saltos de línea a `\r\n` y elimina bytes nulos.
- **Reemite en TCP** a **múltiples clientes simultáneos** (OpenCPN, analizadores, etc.).

Ideal para reemplazar flujos Node-RED cuando solo necesitas **bridge UDP→TCP** con *fan-out* y saneo mínimo del stream.

## Topología

```
[USV / equipo local] -- UDP:20010 --> [Servidor nube NMEA Hub]
                                            ├─ TCP:10110 --> [OpenCPN remoto]
                                            ├─ TCP:10110 --> [Cliente #2]
                                            └─ TCP:10110 --> [Logger/analytics]
```

## Requisitos
- Python **3.8+**
- Linux (Ubuntu/Debian recomendado)
- Permisos para instalar como servicio (systemd)

## Instalación rápida

1) Instala el script:
```bash
sudo mkdir -p /usr/local/bin
sudo cp nmea_hub.py /usr/local/bin/nmea_hub.py
sudo chmod +x /usr/local/bin/nmea_hub.py
```

2) Crea el servicio **systemd**:
```bash
sudo cp nmea-hub.service /etc/systemd/system/nmea-hub.service
sudo systemctl daemon-reload
sudo systemctl enable --now nmea-hub
sudo systemctl status nmea-hub --no-pager
```

3) (Opcional) Abre firewall:
```bash
sudo ufw allow 20010/udp
sudo ufw allow 10110/tcp
```

## Uso
- **Entrada**: enviar NMEA por **UDP** a `IP_SERVIDOR:20010`
- **Salida**: clientes **TCP** (OpenCPN, `nc`, etc.) a `IP_SERVIDOR:10110`

### OpenCPN
1. Opciones → Conexiones → Añadir
2. Protocolo: **TCP**
3. Dirección: `IP_SERVIDOR`
4. Puerto: **10110**
5. Guardar

## Verificación
```bash
# Escuchas activas
ss -ltnup | egrep ':20010|:10110' || true

# Logs
journalctl -u nmea-hub -f
```

Prueba end-to-end:
```bash
# Cliente TCP
nc IP_SERVIDOR 10110

# Inyectar NMEA desde otra consola/host
printf '$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\r\n'   | socat - UDP:IP_SERVIDOR:20010
```

## Configuración
Los puertos por defecto se definen en el encabezado del script (`UDP_PORT`=20010, `TCP_PORT`=10110). Modifícalos según tu topología.

## Seguridad
- Usa **WireGuard** o túneles si expones puertos a Internet.
- Restringe `10110/tcp` a IPs conocidas en firewall.
- Opcional: corre con un **usuario dedicado** y ajusta `User=` en la unit.

## Licencia
MIT License.
