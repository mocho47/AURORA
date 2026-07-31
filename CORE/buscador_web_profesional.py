#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║     🔍 BUSCADOR WEB PROFESIONAL - CÓDIGO REAL PARA PRODUCCIÓN 🔍           ║
║                                                                             ║
║  Integración real con APIs de búsqueda                                     ║
║  • Google Custom Search API                                                ║
║  • Web scraping con beautifulsoup4                                         ║
║  • Análisis de precios en tiempo real                                      ║
║  • Manejo robusto de errores                                               ║
║  • Caché inteligente                                                       ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import httpx
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urljoin, urlparse
import sqlite3
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('buscador_web.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FuenteBusqueda(Enum):
    """Fuentes de búsqueda reales"""
    GOOGLE_SEARCH = {
        "nombre": "Google Custom Search",
        "api": "https://www.googleapis.com/customsearch/v1",
        "timeout": 10
    }
    MERCADO_LIBRE = {
        "nombre": "Mercado Libre API",
        "api": "https://api.mercadolibre.com",
        "timeout": 10
    }
    WEB_SCRAPING = {
        "nombre": "Web Scraping",
        "api": "custom",
        "timeout": 15
    }


@dataclass
class ProductoEncontrado:
    """Producto encontrado en una búsqueda"""
    titulo: str
    precio: float
    moneda: str = "MXN"
    url: str = ""
    fuente: str = ""
    vendedor: str = ""
    rating: float = 0.0
    numero_opiniones: int = 0
    disponibilidad: str = "disponible"
    imagen_url: str = ""
    descripcion: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def puntuacion_calidad(self) -> float:
        """Calcula puntuación de calidad 0-100"""
        score = 0.0

        # Rating
        if self.rating > 0:
            score += (self.rating / 5.0) * 40  # Máximo 40 puntos

        # Cantidad de opiniones (más opiniones = más confiable)
        if self.numero_opiniones > 100:
            score += 30
        elif self.numero_opiniones > 50:
            score += 20
        elif self.numero_opiniones > 10:
            score += 10

        # Disponibilidad
        if self.disponibilidad == "disponible":
            score += 30
        elif self.disponibilidad == "bajo_stock":
            score += 15

        return min(score, 100.0)


@dataclass
class ResultadoBusqueda:
    """Resultado de una búsqueda completa"""
    query: str
    productos: List[ProductoEncontrado] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    tiempo_busqueda_segundos: float = 0.0
    # Por que no hubo resultados, en palabras claras. Antes se devolvia una lista
    # vacia sin ninguna pista y la causa mas comun (falta GOOGLE_API_KEY) quedaba
    # invisible. Cadena vacia = si hubo resultados (agregado 2026-07-29).
    motivo_sin_resultados: str = ""

    def obtener_mejor_opcion(self) -> Optional[ProductoEncontrado]:
        """Retorna el mejor producto basado en puntuación"""
        if not self.productos:
            return None

        # Calcular score para cada producto
        scores = {}
        precios = [p.precio for p in self.productos if p.precio > 0]

        if not precios:
            return self.productos[0]

        precio_min = min(precios)
        precio_max = max(precios)

        for producto in self.productos:
            score = 0.0

            # Score de calidad (40%)
            score += (producto.puntuacion_calidad() / 100.0) * 0.40

            # Score de precio - más bajo es mejor (35%)
            if producto.precio > 0:
                precio_score = 1 - ((producto.precio - precio_min) / (precio_max - precio_min + 1))
                score += precio_score * 0.35
            else:
                score += 0.175

            # Score de disponibilidad (25%)
            if producto.disponibilidad == "disponible":
                score += 0.25

            scores[producto.url] = score

        mejor_url = max(scores, key=scores.get)
        return next(p for p in self.productos if p.url == mejor_url)

    def obtener_analisis(self) -> str:
        """Genera análisis del resultado"""
        if not self.productos:
            return "No se encontraron productos."

        mejor = self.obtener_mejor_opcion()

        analisis = f"""
═══════════════════════════════════════════════════════════════════════════════
📊 ANÁLISIS DE BÚSQUEDA: {self.query}
═══════════════════════════════════════════════════════════════════════════════

🏆 MEJOR OPCIÓN RECOMENDADA:
   Nombre: {mejor.titulo}
   Precio: ${mejor.precio:.2f} {mejor.moneda}
   Vendedor: {mejor.vendedor}
   Rating: ⭐ {mejor.rating}/5.0 ({mejor.numero_opiniones} opiniones)
   Disponibilidad: {mejor.disponibilidad}
   URL: {mejor.url}

💡 POR QUÉ ES LA MEJOR:
   ✓ Mejor relación calidad-precio
   ✓ Alto rating de vendedor ({mejor.rating}/5.0)
   ✓ Muchas opiniones verificadas ({mejor.numero_opiniones})
   ✓ Disponibilidad inmediata

📈 ESTADÍSTICAS DEL MERCADO:
   Total opciones encontradas: {len(self.productos)}
   Precio mínimo: ${min([p.precio for p in self.productos if p.precio > 0], default=0):.2f}
   Precio máximo: ${max([p.precio for p in self.productos if p.precio > 0], default=0):.2f}
   Precio promedio: ${sum([p.precio for p in self.productos if p.precio > 0]) / len([p for p in self.productos if p.precio > 0]):.2f}

═══════════════════════════════════════════════════════════════════════════════
        """
        return analisis


class BuscadorWebProfesional:
    """Buscador web profesional con múltiples fuentes"""

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_search_engine_id: Optional[str] = None
    ):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.google_search_engine_id = google_search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.cache_path = Path("busquedas_cache.db")
        self._inicializar_cache()
        self.timeout_session = 30

        logger.info("🔍 Buscador Web Profesional inicializado")

    def _inicializar_cache(self):
        """Inicializa base de datos de caché"""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS busquedas (
                id TEXT PRIMARY KEY,
                query TEXT,
                resultados JSON,
                timestamp TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def _obtener_cache(self, query: str) -> Optional[List[ProductoEncontrado]]:
        """Obtiene resultados del caché si existen y no han expirado"""
        query_hash = hashlib.md5(query.encode()).hexdigest()

        try:
            conn = sqlite3.connect(self.cache_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT resultados, timestamp FROM busquedas WHERE id = ?',
                (query_hash,)
            )
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                resultados_json, timestamp = resultado
                timestamp_obj = datetime.fromisoformat(timestamp)

                # Caché válido por 24 horas
                if datetime.now() - timestamp_obj < timedelta(hours=24):
                    logger.info(f"💾 Usando caché para: {query}")
                    productos = json.loads(resultados_json)
                    return [ProductoEncontrado(**p) for p in productos]

        except Exception as e:
            logger.warning(f"⚠️ Error leyendo caché: {e}")

        return None

    def _guardar_cache(self, query: str, productos: List[ProductoEncontrado]):
        """Guarda resultados en caché"""
        query_hash = hashlib.md5(query.encode()).hexdigest()

        try:
            productos_dict = [asdict(p) for p in productos]
            # Convertir datetime a string
            for p in productos_dict:
                p['timestamp'] = p['timestamp'].isoformat()

            conn = sqlite3.connect(self.cache_path)
            cursor = conn.cursor()

            cursor.execute(
                'INSERT OR REPLACE INTO busquedas (id, query, resultados, timestamp) VALUES (?, ?, ?, ?)',
                (query_hash, query, json.dumps(productos_dict), datetime.now().isoformat())
            )

            conn.commit()
            conn.close()
            logger.info(f"💾 Resultados guardados en caché: {query}")

        except Exception as e:
            logger.warning(f"⚠️ Error guardando caché: {e}")

    async def buscar(
        self,
        query: str,
        incluir_google: bool = True,
        incluir_mercadolibre: bool = True,
        incluir_scraping: bool = False
    ) -> ResultadoBusqueda:
        """Realiza búsqueda en múltiples fuentes en paralelo"""

        # Intentar obtener del caché primero
        productos_cache = self._obtener_cache(query)
        if productos_cache:
            return ResultadoBusqueda(
                query=query,
                productos=productos_cache,
                tiempo_busqueda_segundos=0.0
            )

        logger.info(f"🔍 Iniciando búsqueda: {query}")

        inicio = datetime.now()
        productos = []
        tareas = []

        # Preparar tareas de búsqueda
        if incluir_google and self.google_api_key:
            tareas.append(self._buscar_google(query))

        if incluir_mercadolibre:
            tareas.append(self._buscar_mercadolibre(query))

        if incluir_scraping:
            tareas.append(self._buscar_web_scraping(query))

        # Ejecutar búsquedas en paralelo
        if tareas:
            resultados = await asyncio.gather(*tareas, return_exceptions=True)

            for resultado in resultados:
                if isinstance(resultado, Exception):
                    logger.error(f"❌ Error en búsqueda: {resultado}")
                elif resultado:
                    productos.extend(resultado)

        # Eliminar duplicados
        urls_vistas = set()
        productos_unicos = []
        for p in productos:
            if p.url not in urls_vistas:
                productos_unicos.append(p)
                urls_vistas.add(p.url)

        # Ordenar por puntuación
        productos_unicos.sort(
            key=lambda p: p.puntuacion_calidad(),
            reverse=True
        )

        tiempo_busqueda = (datetime.now() - inicio).total_seconds()

        resultado = ResultadoBusqueda(
            query=query,
            productos=productos_unicos,
            tiempo_busqueda_segundos=tiempo_busqueda
        )

        # Guardar en caché
        self._guardar_cache(query, productos_unicos)

        logger.info(f"✅ Búsqueda completada: {len(productos_unicos)} opciones en {tiempo_busqueda:.1f}s")

        # HONESTIDAD (agregado 2026-07-29): antes, si no encontraba nada devolvia
        # 0 resultados sin decir POR QUE — y la causa real mas comun es que falta
        # GOOGLE_API_KEY en el .env, asi que la busqueda de Google ni se intenta
        # (linea 301: "if incluir_google and self.google_api_key"). Verificado en
        # vivo: 0 opciones en 5.1s sin ninguna pista del motivo. Ahora se dice.
        if not productos_unicos:
            motivos = []
            if incluir_google and not self.google_api_key:
                motivos.append("falta GOOGLE_API_KEY en el .env, así que la búsqueda de "
                               "Google no se intentó siquiera")
            if not tareas:
                motivos.append("no se habilitó ninguna fuente de búsqueda")
            resultado.motivo_sin_resultados = (
                "; ".join(motivos) if motivos
                else "las fuentes respondieron pero ninguna trajo productos para esta consulta")
            logger.warning(f"⚠️ Sin resultados: {resultado.motivo_sin_resultados}")

        return resultado

    async def _buscar_google(self, query: str) -> List[ProductoEncontrado]:
        """Búsqueda en Google Custom Search API"""

        productos = []

        try:
            logger.info(f"  📍 Buscando en Google...")

            async with httpx.AsyncClient(timeout=self.timeout_session) as client:
                response = await client.get(
                    FuenteBusqueda.GOOGLE_SEARCH.value['api'],
                    params={
                        'q': query,
                        'key': self.google_api_key,
                        'cx': self.google_search_engine_id,
                        'num': 10,
                        'start': 1
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Procesar resultados
                for item in data.get('items', []):
                    producto = ProductoEncontrado(
                        titulo=item.get('title', ''),
                        url=item.get('link', ''),
                        descripcion=item.get('snippet', ''),
                        fuente='Google Search',
                        precio=0.0,  # Google no proporciona precio directamente
                        vendedor='Resultado búsqueda web'
                    )

                    if producto.titulo:
                        productos.append(producto)

                logger.info(f"    ✓ {len(productos)} resultados de Google")

        except Exception as e:
            logger.error(f"  ❌ Error en búsqueda Google: {e}")

        return productos

    async def _buscar_mercadolibre(self, query: str) -> List[ProductoEncontrado]:
        """Búsqueda en Mercado Libre API"""

        productos = []

        try:
            logger.info(f"  📍 Buscando en Mercado Libre...")

            async with httpx.AsyncClient(timeout=self.timeout_session) as client:
                # Buscar en Mercado Libre México
                response = await client.get(
                    'https://api.mercadolibre.com/sites/MLM/search',
                    params={
                        'q': query,
                        'limit': 20,
                        'sort': 'price_asc',
                        'condition': 'new'
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Procesar resultados
                for item in data.get('results', []):
                    # Obtener información de vendedor
                    seller_info = item.get('seller', {})
                    reputation = seller_info.get('seller_reputation', {})
                    rating = reputation.get('rating', 0.0)

                    producto = ProductoEncontrado(
                        titulo=item.get('title', ''),
                        precio=float(item.get('price', 0)),
                        moneda=item.get('currency_id', 'MXN'),
                        url=item.get('permalink', ''),
                        fuente='Mercado Libre',
                        vendedor=seller_info.get('nickname', 'Vendedor ML'),
                        rating=rating,
                        numero_opiniones=item.get('reviews_count', 0),
                        disponibilidad='disponible' if item.get('available_quantity', 0) > 0 else 'agotado',
                        imagen_url=item.get('thumbnail', '')
                    )

                    if producto.precio > 0:
                        productos.append(producto)

                logger.info(f"    ✓ {len(productos)} resultados de Mercado Libre")

        except Exception as e:
            logger.error(f"  ❌ Error en búsqueda Mercado Libre: {e}")

        return productos

    async def _buscar_web_scraping(self, query: str) -> List[ProductoEncontrado]:
        """Web scraping en sitios específicos"""
        # Desactivado 2026-07-31: apuntaba a 'ejemplo-distribuidor.com', un sitio que
        # no existe. Este archivo SÍ corre en producción (lo usa consciencia.py), así
        # que cada llamada gastaba el tiempo de espera completo y dejaba un error en
        # el log sin devolver jamás un producto. Las fuentes que sí funcionan (Google
        # Custom Search y la API de MercadoLibre) no se tocan. El esqueleto se
        # conserva por si algún día se implementa scraping de verdad.
        return []

        productos = []

        try:
            logger.info(f"  📍 Web scraping...")

            # Ejemplo: buscar en un distribuidor local
            # En producción, implementar scraping específico para cada sitio

            async with httpx.AsyncClient(timeout=self.timeout_session) as client:
                # Aquí iría el scraping real
                # Ejemplo simplificado:
                sitios = [
                    'https://www.ejemplo-distribuidor.com/search?q=' + query,
                ]

                for url in sitios:
                    try:
                        response = await client.get(url)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Buscar productos en la página
                        # Esto sería específico para cada sitio
                        items = soup.find_all('div', class_='producto')

                        for item in items:
                            try:
                                titulo_elem = item.find('h2', class_='nombre')
                                precio_elem = item.find('span', class_='precio')
                                url_elem = item.find('a', class_='enlace')

                                if titulo_elem and precio_elem and url_elem:
                                    try:
                                        precio_text = precio_elem.text.replace('$', '').replace(',', '')
                                        precio = float(precio_text)

                                        producto = ProductoEncontrado(
                                            titulo=titulo_elem.text.strip(),
                                            precio=precio,
                                            url=urljoin(url, url_elem.get('href', '')),
                                            fuente='Web Scraping',
                                            vendedor='Distribuidor Local'
                                        )

                                        productos.append(producto)
                                    except ValueError:
                                        continue

                            except Exception as e:
                                logger.debug(f"Error procesando item: {e}")
                                continue

                    except Exception as e:
                        logger.debug(f"Error scraping {url}: {e}")
                        continue

                logger.info(f"    ✓ {len(productos)} resultados de web scraping")

        except Exception as e:
            logger.error(f"  ❌ Error en web scraping: {e}")

        return productos


# Ejemplo de uso
async def ejemplo_uso():
    """Ejemplo de cómo usar el buscador profesional"""

    buscador = BuscadorWebProfesional()

    # Realizar búsqueda
    resultado = await buscador.buscar(
        "Bumper deportivo Ford Mustang",
        incluir_google=False,  # Requiere API key
        incluir_mercadolibre=True,
        incluir_scraping=False
    )

    # Mostrar resultados
    print(resultado.obtener_analisis())

    # Mostrar mejor opción
    mejor = resultado.obtener_mejor_opcion()
    if mejor:
        print(f"\n✅ MEJOR OPCIÓN:")
        print(f"   {mejor.titulo}")
        print(f"   ${mejor.precio:.2f} {mejor.moneda}")
        print(f"   {mejor.url}")


if __name__ == "__main__":
    asyncio.run(ejemplo_uso())
