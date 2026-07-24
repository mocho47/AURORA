"""
AURORA SYNC - Sincronización bidireccional multi-PC
Tu PC ←→ PC esposa (sincronización en tiempo real)
"""

import asyncio
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import websockets
from dataclasses import dataclass, asdict


@dataclass
class CambioSync:
    """Representa un cambio a sincronizar"""
    timestamp: str
    tipo: str  # "archivo", "base_datos", "memoria", "config"
    ruta: str
    operacion: str  # "crear", "actualizar", "eliminar"
    hash_contenido: str
    pc_origen: str  # "tu_pc" o "pc_esposa"
    prioridad: int = 1


class AuroraSync:
    """
    Sincronización bidireccional entre PCs

    Tu PC (Master) ←→ PC Esposa (Replica)

    Flujo:
    1. Detecta cambios locales cada 5 segundos
    2. Envía cambios a otra PC
    3. Recibe cambios de otra PC
    4. Resuelve conflictos (timestamp o manual)
    5. Aplica cambios sincronizados
    """

    def __init__(self, config_path: str = "C:/AURORA/SYNC/sync_config.json"):
        self.config = self._cargar_config(config_path)
        self.tu_pc = self.config.get("tu_pc")
        self.pc_esposa = self.config.get("pc_esposa")
        self.puerto_sync = self.config.get("puerto_sync", 9000)

        # Colas de cambios
        self.cambios_locales: List[CambioSync] = []
        self.cambios_remotos: List[CambioSync] = []
        self.conflictos: List[Tuple[CambioSync, CambioSync]] = []

        # Estado de conexión
        self.conectado = False
        self.ultimo_sync = datetime.now()
        self.modo = "bidireccional"

        # Monitorear directorios
        self.directorios_monitoreo = [
            "C:/AURORA/DATA/",
            "C:/AURORA/MEMORIA/",
            "C:/AURORA/SYNC/",
            "C:/AURORA/MOTORES/output/",
        ]

        # Inicializar sincronización
        self._inicializar_sincronizacion()

    def _cargar_config(self, ruta: str) -> Dict:
        """Carga configuración de sincronización"""

        Path(ruta).parent.mkdir(parents=True, exist_ok=True)

        if Path(ruta).exists():
            with open(ruta) as f:
                return json.load(f)

        # Config por defecto
        config = {
            "tu_pc": {
                "nombre": "Tu PC",
                "ip": "192.168.1.100",
                "puerto": 9000,
                "tipo": "master"
            },
            "pc_esposa": {
                "nombre": "PC Esposa",
                "ip": "192.168.1.101",
                "puerto": 9000,
                "tipo": "replica"
            },
            "puerto_sync": 9000,
            "intervalo_sync": 5,  # segundos
            "resolver_conflictos": "timestamp"  # timestamp o manual
        }

        # Guardar
        with open(ruta, "w") as f:
            json.dump(config, f, indent=2)

        return config

    async def sincronizar(self):
        """
        Ejecuta sincronización completa

        Ciclo:
        1. Detectar cambios locales
        2. Conectar con PC remota
        3. Enviar cambios locales
        4. Recibir cambios remotos
        5. Resolver conflictos
        6. Aplicar cambios
        7. Guardar estado
        """

        print("[SYNC] Iniciando sincronización...")

        # Paso 1: Detectar cambios locales
        self.cambios_locales = await self._detectar_cambios_locales()

        if self.cambios_locales:
            print(f"[SYNC] Detectados {len(self.cambios_locales)} cambios locales")

        # Paso 2-3: Enviar cambios a PC remota
        if self.cambios_locales:
            await self._enviar_cambios(self.cambios_locales)

        # Paso 4: Recibir cambios de PC remota
        self.cambios_remotos = await self._recibir_cambios()

        if self.cambios_remotos:
            print(f"[SYNC] Recibidos {len(self.cambios_remotos)} cambios remotos")

        # Paso 5: Resolver conflictos
        self.conflictos = await self._detectar_conflictos()

        if self.conflictos:
            print(f"[SYNC] Detectados {len(self.conflictos)} conflictos")
            await self._resolver_conflictos()

        # Paso 6: Aplicar cambios
        await self._aplicar_cambios()

        # Paso 7: Guardar estado
        self._guardar_estado_sync()

        print("[SYNC] Sincronización completada")

    async def _detectar_cambios_locales(self) -> List[CambioSync]:
        """
        Detecta cambios en directorios locales

        Compara hash de archivos con último sync
        """

        cambios = []

        for directorio in self.directorios_monitoreo:
            ruta = Path(directorio)

            if not ruta.exists():
                continue

            # Recorrer archivos
            for archivo in ruta.rglob("*"):
                if archivo.is_file():
                    # Calcular hash actual
                    hash_actual = self._calcular_hash(archivo)

                    # Comparar con hash guardado
                    hash_anterior = self._obtener_hash_anterior(archivo)

                    if hash_actual != hash_anterior:
                        # Nuevo cambio detectado
                        cambios.append(CambioSync(
                            timestamp=datetime.now().isoformat(),
                            tipo=self._detectar_tipo_archivo(archivo),
                            ruta=str(archivo),
                            operacion="actualizar",
                            hash_contenido=hash_actual,
                            pc_origen=self.tu_pc["nombre"],
                            prioridad=self._calcular_prioridad(archivo)
                        ))

        return cambios

    async def _enviar_cambios(self, cambios: List[CambioSync]):
        """
        Envía cambios a PC remota via WebSocket
        """

        try:
            ws_url = f"ws://{self.pc_esposa['ip']}:{self.puerto_sync}"

            async with websockets.connect(ws_url, ping_interval=None) as websocket:
                for cambio in cambios:
                    # Preparar mensaje
                    mensaje = {
                        "tipo": "cambio_sync",
                        "cambio": asdict(cambio),
                        "contenido_b64": self._leer_archivo_b64(cambio.ruta)
                    }

                    # Enviar
                    await websocket.send(json.dumps(mensaje))
                    print(f"[SYNC] Enviado: {cambio.ruta}")

            self.conectado = True

        except Exception as e:
            print(f"[SYNC] Error enviando cambios: {e}")
            self.conectado = False

    async def _recibir_cambios(self) -> List[CambioSync]:
        """
        Recibe cambios de PC remota via WebSocket
        """

        cambios = []

        try:
            # Servidor WebSocket escuchando
            async with websockets.serve(self._manejar_conexion_sync, "0.0.0.0", self.puerto_sync):
                await asyncio.sleep(1)  # Escuchar 1 segundo

        except Exception as e:
            print(f"[SYNC] Error recibiendo cambios: {e}")

        return cambios

    async def _manejar_conexion_sync(self, websocket, path):
        """Maneja conexión WebSocket entrante"""

        try:
            async for mensaje in websocket:
                datos = json.loads(mensaje)

                if datos.get("tipo") == "cambio_sync":
                    # Procesar cambio remoto
                    cambio_dict = datos.get("cambio")
                    cambio = CambioSync(**cambio_dict)

                    contenido_b64 = datos.get("contenido_b64")

                    # Agregar a cola
                    self.cambios_remotos.append(cambio)

                    # Guardar archivo
                    self._escribir_archivo_b64(cambio.ruta, contenido_b64)

                    print(f"[SYNC] Recibido: {cambio.ruta}")

        except Exception as e:
            print(f"[SYNC] Error en conexión: {e}")

    async def _detectar_conflictos(self) -> List[Tuple[CambioSync, CambioSync]]:
        """
        Detecta conflictos (mismo archivo modificado en ambas PCs)
        """

        conflictos = []

        for cambio_local in self.cambios_locales:
            for cambio_remoto in self.cambios_remotos:
                if cambio_local.ruta == cambio_remoto.ruta:
                    # Mismo archivo modificado en ambas PCs
                    if cambio_local.timestamp != cambio_remoto.timestamp:
                        conflictos.append((cambio_local, cambio_remoto))

        return conflictos

    async def _resolver_conflictos(self):
        """
        Resuelve conflictos automáticamente

        Estrategia: Last-write-wins (timestamp más reciente)
        """

        for conflicto_local, conflicto_remoto in self.conflictos:
            timestamp_local = datetime.fromisoformat(conflicto_local.timestamp)
            timestamp_remoto = datetime.fromisoformat(conflicto_remoto.timestamp)

            if timestamp_local > timestamp_remoto:
                # Versión local gana
                print(f"[SYNC] Conflicto resuelto: Local ganador ({conflicto_local.ruta})")
                # Enviar versión local a PC remota
                await self._enviar_cambios([conflicto_local])

            else:
                # Versión remota gana
                print(f"[SYNC] Conflicto resuelto: Remoto ganador ({conflicto_remoto.ruta})")
                # Guardar versión remota localmente (ya está)
                pass

    async def _aplicar_cambios(self):
        """
        Aplica cambios sincronizados al sistema local

        Para cada cambio remoto que no está en conflicto:
        - Crear/actualizar/eliminar archivo
        - Actualizar base de datos
        - Recargar memoria generativa
        """

        for cambio in self.cambios_remotos:
            # Saltar si está en conflicto resuelto
            if any(c[1].ruta == cambio.ruta for c in self.conflictos):
                continue

            try:
                if cambio.operacion == "crear" or cambio.operacion == "actualizar":
                    # Ya está guardado en _recibir_cambios
                    print(f"[SYNC] Aplicado: {cambio.ruta}")

                elif cambio.operacion == "eliminar":
                    ruta = Path(cambio.ruta)
                    if ruta.exists():
                        ruta.unlink()
                        print(f"[SYNC] Eliminado: {cambio.ruta}")

                # Si es base de datos o memoria, recargar
                if "DATA/" in cambio.ruta or "MEMORIA/" in cambio.ruta:
                    print(f"[SYNC] Recargando contexto: {cambio.tipo}")

            except Exception as e:
                print(f"[SYNC] Error aplicando cambio {cambio.ruta}: {e}")

    def _guardar_estado_sync(self):
        """Guarda estado de sincronización"""

        estado = {
            "timestamp": datetime.now().isoformat(),
            "cambios_locales": len(self.cambios_locales),
            "cambios_remotos": len(self.cambios_remotos),
            "conflictos_resueltos": len(self.conflictos),
            "conectado": self.conectado,
            "directorio_sync": "C:/AURORA/SYNC/"
        }

        ruta = Path("C:/AURORA/SYNC/sync_state.json")
        ruta.parent.mkdir(parents=True, exist_ok=True)

        with open(ruta, "w") as f:
            json.dump(estado, f, indent=2)

    # ==================== MÉTODOS UTILITARIOS ====================

    def _calcular_hash(self, archivo: Path) -> str:
        """Calcula hash SHA256 de archivo"""

        sha256_hash = hashlib.sha256()

        with open(archivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _obtener_hash_anterior(self, archivo: Path) -> str:
        """Obtiene hash guardado de sync anterior"""

        # Buscar en sync_state.json o archivo de hashes
        ruta_hashes = Path("C:/AURORA/SYNC/file_hashes.json")

        if ruta_hashes.exists():
            with open(ruta_hashes) as f:
                hashes = json.load(f)
                return hashes.get(str(archivo), "")

        return ""

    def _detectar_tipo_archivo(self, archivo: Path) -> str:
        """Detecta tipo de cambio según ruta"""

        ruta_str = str(archivo)

        if "DATA/" in ruta_str:
            return "base_datos"
        elif "MEMORIA/" in ruta_str:
            return "memoria"
        elif "SYNC/" in ruta_str:
            return "config"
        else:
            return "archivo"

    def _calcular_prioridad(self, archivo: Path) -> int:
        """Calcula prioridad de sincronización"""

        ruta_str = str(archivo)

        if "MEMORIA/" in ruta_str:
            return 3  # Alta (memoria es crítica)
        elif "DATA/" in ruta_str and "pedidos" in ruta_str:
            return 2  # Media-alta (pedidos importante)
        else:
            return 1  # Normal

    def _leer_archivo_b64(self, ruta: str) -> str:
        """Lee archivo y lo codifica en base64"""

        import base64

        try:
            with open(ruta, "rb") as f:
                contenido = f.read()
                return base64.b64encode(contenido).decode()
        except:
            return ""

    def _escribir_archivo_b64(self, ruta: str, contenido_b64: str):
        """Escribe archivo desde base64"""

        import base64

        try:
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)

            contenido = base64.b64decode(contenido_b64)

            with open(ruta, "wb") as f:
                f.write(contenido)
        except Exception as e:
            print(f"[SYNC] Error escribiendo archivo {ruta}: {e}")

    def _inicializar_sincronizacion(self):
        """Inicializa directorios y archivos necesarios"""

        directorios = [
            "C:/AURORA/SYNC/",
            "C:/AURORA/MEMORIA/",
            "C:/AURORA/DATA/",
        ]

        for directorio in directorios:
            Path(directorio).mkdir(parents=True, exist_ok=True)

        # Crear archivo de hashes si no existe
        ruta_hashes = Path("C:/AURORA/SYNC/file_hashes.json")

        if not ruta_hashes.exists():
            with open(ruta_hashes, "w") as f:
                json.dump({}, f)


# Instancia global
sync = AuroraSync()


async def main():
    """Ejecuta sincronización continua"""

    print("[SYNC] AURORA Sincronización iniciada")
    print(f"[SYNC] Tu PC: {sync.tu_pc['nombre']} ({sync.tu_pc['ip']})")
    print(f"[SYNC] PC Esposa: {sync.pc_esposa['nombre']} ({sync.pc_esposa['ip']})")

    # Loop de sincronización cada 5 segundos
    while True:
        await sync.sincronizar()
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
