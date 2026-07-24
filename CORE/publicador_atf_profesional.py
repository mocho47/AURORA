#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║     🔗 PUBLICADOR ATF PROFESIONAL - CÓDIGO REAL PARA PRODUCCIÓN 🔗         ║
║                                                                             ║
║  Integración real con APIs de redes sociales                               ║
║  • Autenticación OAuth2 real                                               ║
║  • Publicación real en plataformas                                         ║
║  • Manejo robusto de errores y reintentos                                  ║
║  • Logging profesional                                                     ║
║  • Validaciones estrictas                                                  ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import logging
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid
from pathlib import Path
import httpx

# Configurar logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('publicador_atf.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RedSocial(Enum):
    """Redes sociales soportadas con credenciales reales"""
    TIKTOK = {
        "nombre": "TikTok",
        "api_endpoint": "https://open.tiktokapis.com/v1",
        "oauth_endpoint": "https://www.tiktok.com/v1/oauth/authorize",
        "token_endpoint": "https://open.tiktokapis.com/v1/oauth/token",
        "max_duracion": 600,
        "max_tamanio_mb": 287.6,
        "formatos": ["mp4", "mov"]
    }
    INSTAGRAM = {
        "nombre": "Instagram",
        "api_endpoint": "https://graph.instagram.com/v18.0",
        "oauth_endpoint": "https://api.instagram.com/oauth/authorize",
        "token_endpoint": "https://graph.instagram.com/v18.0/oauth/access_token",
        "max_duracion": 60,
        "max_tamanio_mb": 4095,
        "formatos": ["mp4", "mov"]
    }
    YOUTUBE = {
        "nombre": "YouTube",
        "api_endpoint": "https://www.googleapis.com/youtube/v3",
        "oauth_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "max_duracion": 12 * 3600,
        "max_tamanio_mb": 256000,
        "formatos": ["mp4", "mkv", "mov", "avi"]
    }
    FACEBOOK = {
        "nombre": "Facebook",
        "api_endpoint": "https://graph.facebook.com/v18.0",
        "oauth_endpoint": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_endpoint": "https://graph.facebook.com/v18.0/oauth/access_token",
        "max_duracion": 240,
        "max_tamanio_mb": 4000,
        "formatos": ["mp4", "mov"]
    }


@dataclass
class CredencialesRed:
    """Credenciales OAuth2 para una red social"""
    red: RedSocial
    access_token: str
    refresh_token: Optional[str] = None
    token_expira: Optional[datetime] = None
    scope: str = ""
    user_id: str = ""
    username: str = ""
    cuenta_verificada: bool = False

    def token_valido(self) -> bool:
        """Verifica si el token sigue siendo válido"""
        if not self.token_expira:
            return True
        # Renovar si falta menos de 5 minutos
        return datetime.now() < (self.token_expira - timedelta(minutes=5))

    async def renovar_token_si_necesario(self, client_id: str, client_secret: str) -> bool:
        """Renueva el token si está expirado"""
        if self.token_valido():
            return True

        if not self.refresh_token:
            logger.error(f"❌ No hay refresh token para {self.red.value['nombre']}")
            return False

        logger.info(f"🔄 Renovando token para {self.red.value['nombre']}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.red.value['token_endpoint'],
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                expires_in = data.get("expires_in", 3600)
                self.token_expira = datetime.now() + timedelta(seconds=expires_in)

                logger.info(f"✅ Token renovado para {self.red.value['nombre']}")
                return True

        except Exception as e:
            logger.error(f"❌ Error renovando token: {e}")
            return False


@dataclass
class ConfiguracionPublicacion:
    """Configuración para publicar contenido"""
    titulo: str
    descripcion: str
    archivo_video_path: str
    redes: List[RedSocial]
    captions_personalizados: Dict[str, str] = field(default_factory=dict)
    hashtags: Dict[str, List[str]] = field(default_factory=dict)
    horario_publicacion: Optional[datetime] = None
    permitir_comentarios: bool = True
    permitir_compartidos: bool = True

    def validar(self) -> Tuple[bool, str]:
        """Valida la configuración"""
        # Verificar archivo
        if not os.path.exists(self.archivo_video_path):
            return False, f"Archivo no existe: {self.archivo_video_path}"

        # Verificar tamaño
        tamanio_mb = os.path.getsize(self.archivo_video_path) / (1024 * 1024)
        for red in self.redes:
            max_mb = red.value['max_tamanio_mb']
            if tamanio_mb > max_mb:
                return False, f"Archivo demasiado grande para {red.value['nombre']} ({tamanio_mb:.1f}MB > {max_mb}MB)"

        # Verificar redes válidas
        if not self.redes:
            return False, "Debe especificar al menos una red"

        return True, "Configuración válida"


@dataclass
class ResultadoPublicacion:
    """Resultado de una publicación en una red"""
    red: RedSocial
    exitoso: bool
    id_post: Optional[str] = None
    url_post: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metricas_iniciales: Dict[str, Any] = field(default_factory=dict)


class PublicadorATFProfesional:
    """Publicador profesional para ATF con APIs reales"""

    def __init__(
        self,
        credenciales_redes: Dict[RedSocial, CredencialesRed],
        client_id: str = "",
        client_secret: str = ""
    ):
        self.credenciales = credenciales_redes
        self.client_id = client_id or os.getenv("OAUTH_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("OAUTH_CLIENT_SECRET", "")
        self.historial_publicaciones: List[ResultadoPublicacion] = []
        self.sesion: Optional[aiohttp.ClientSession] = None

        logger.info("🔗 Publicador ATF Profesional inicializado")

    async def __aenter__(self):
        """Context manager entry"""
        self.sesion = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.sesion:
            await self.sesion.close()

    async def verificar_credenciales(self) -> Dict[RedSocial, bool]:
        """Verifica y renueva credenciales si es necesario"""
        logger.info("🔐 Verificando credenciales...")
        resultados = {}

        for red, cred in self.credenciales.items():
            try:
                # Renovar si es necesario
                renovada = await cred.renovar_token_si_necesario(
                    self.client_id,
                    self.client_secret
                )

                if not renovada and not cred.token_valido():
                    resultados[red] = False
                    logger.warning(f"⚠️ Credencial inválida para {red.value['nombre']}")
                else:
                    resultados[red] = True
                    logger.info(f"✅ {red.value['nombre']}: Credenciales válidas")

            except Exception as e:
                logger.error(f"❌ Error verificando {red.value['nombre']}: {e}")
                resultados[red] = False

        return resultados

    async def publicar_multi_red(
        self,
        config: ConfiguracionPublicacion
    ) -> Dict[RedSocial, ResultadoPublicacion]:
        """Publica en múltiples redes simultáneamente"""

        # Validar configuración
        valida, mensaje = config.validar()
        if not valida:
            logger.error(f"❌ Configuración inválida: {mensaje}")
            return {}

        logger.info(f"📤 Iniciando publicación multi-red")
        logger.info(f"   Título: {config.titulo}")
        logger.info(f"   Redes: {', '.join([r.value['nombre'] for r in config.redes])}")

        # Verificar credenciales
        creds_ok = await self.verificar_credenciales()

        # Publicar en paralelo
        tareas = {
            red: self._publicar_en_red(red, config)
            for red in config.redes
            if creds_ok.get(red, False)
        }

        resultados = {}
        for red, tarea in tareas.items():
            resultado = await tarea
            resultados[red] = resultado
            self.historial_publicaciones.append(resultado)

        # Resumen
        exitosas = sum(1 for r in resultados.values() if r.exitoso)
        logger.info(f"\n✅ Publicación completada")
        logger.info(f"   Exitosas: {exitosas}/{len(resultados)}")

        return resultados

    async def _publicar_en_red(
        self,
        red: RedSocial,
        config: ConfiguracionPublicacion
    ) -> ResultadoPublicacion:
        """Publica en una red específica"""

        resultado = ResultadoPublicacion(red=red, exitoso=False)
        cred = self.credenciales[red]

        try:
            logger.info(f"\n📍 Publicando en {red.value['nombre']}...")

            # Obtener caption personalizado
            caption = config.captions_personalizados.get(
                red.value['nombre'],
                config.descripcion
            )

            # Obtener hashtags
            hashtags = config.hashtags.get(red.value['nombre'], [])
            caption_final = f"{caption}\n\n{' '.join(hashtags)}"

            # Publicar según la red
            if red == RedSocial.TIKTOK:
                resultado = await self._publicar_tiktok(cred, config, caption_final)

            elif red == RedSocial.INSTAGRAM:
                resultado = await self._publicar_instagram(cred, config, caption_final)

            elif red == RedSocial.YOUTUBE:
                resultado = await self._publicar_youtube(cred, config, caption_final)

            elif red == RedSocial.FACEBOOK:
                resultado = await self._publicar_facebook(cred, config, caption_final)

            if resultado.exitoso:
                logger.info(f"✅ {red.value['nombre']}: Publicado")
                logger.info(f"   ID: {resultado.id_post}")
                logger.info(f"   URL: {resultado.url_post}")
            else:
                logger.error(f"❌ {red.value['nombre']}: {resultado.error}")

        except Exception as e:
            logger.error(f"❌ Error publicando en {red.value['nombre']}: {e}")
            resultado.exitoso = False
            resultado.error = str(e)

        return resultado

    async def _publicar_tiktok(
        self,
        cred: CredencialesRed,
        config: ConfiguracionPublicacion,
        caption: str
    ) -> ResultadoPublicacion:
        """Publica en TikTok usando API real"""

        resultado = ResultadoPublicacion(red=RedSocial.TIKTOK, exitoso=False)

        try:
            async with httpx.AsyncClient() as client:
                # Paso 1: Iniciar upload
                upload_url = f"{RedSocial.TIKTOK.value['api_endpoint']}/video/upload/init"

                init_response = await client.post(
                    upload_url,
                    headers={"Authorization": f"Bearer {cred.access_token}"},
                    json={
                        "source_info": {
                            "source": "FILE_UPLOAD",
                            "platform": "TikTok"
                        },
                        "video_size": os.path.getsize(config.archivo_video_path),
                        "chunk_total_count": 1,
                        "upload_type": "web_upload"
                    },
                    timeout=30.0
                )

                init_response.raise_for_status()
                init_data = init_response.json()

                if init_data.get("data", {}).get("error"):
                    raise Exception(f"TikTok upload init error: {init_data}")

                upload_token = init_data["data"]["upload_token"]
                upload_address = init_data["data"]["upload_address"]

                # Paso 2: Subir archivo
                with open(config.archivo_video_path, 'rb') as f:
                    files = {'chunk_file': f}
                    upload_response = await client.post(
                        upload_address,
                        files=files,
                        data={
                            'upload_token': upload_token,
                            'chunk_seq': 0
                        },
                        timeout=60.0
                    )
                    upload_response.raise_for_status()

                # Paso 3: Crear post
                create_url = f"{RedSocial.TIKTOK.value['api_endpoint']}/video/publish"

                create_response = await client.post(
                    create_url,
                    headers={"Authorization": f"Bearer {cred.access_token}"},
                    json={
                        "data": {
                            "upload_token": upload_token,
                            "description": caption,
                            "privacy_level": "PUBLIC_TO_EVERYONE",
                            "video_cover_timestamp_ms": 0,
                            "disable_comment": not config.permitir_comentarios,
                            "disable_duet": False,
                            "disable_stitch": False,
                        }
                    },
                    timeout=30.0
                )

                create_response.raise_for_status()
                create_data = create_response.json()

                if create_data.get("error"):
                    raise Exception(f"TikTok publish error: {create_data}")

                resultado.exitoso = True
                resultado.id_post = create_data["data"]["video_id"]
                resultado.url_post = f"https://www.tiktok.com/@{cred.username}/video/{resultado.id_post}"
                resultado.metricas_iniciales = {"views": 0, "likes": 0, "comments": 0}

        except Exception as e:
            resultado.error = str(e)
            logger.error(f"TikTok error: {e}")

        return resultado

    async def _publicar_instagram(
        self,
        cred: CredencialesRed,
        config: ConfiguracionPublicacion,
        caption: str
    ) -> ResultadoPublicacion:
        """Publica en Instagram usando API real"""

        resultado = ResultadoPublicacion(red=RedSocial.INSTAGRAM, exitoso=False)

        try:
            async with httpx.AsyncClient() as client:
                # Paso 1: Crear media container
                media_url = f"{RedSocial.INSTAGRAM.value['api_endpoint']}/{cred.user_id}/media"

                media_response = await client.post(
                    media_url,
                    headers={"Authorization": f"Bearer {cred.access_token}"},
                    params={
                        "media_type": "REELS",
                        "video_url": f"file://{config.archivo_video_path}",
                        "caption": caption,
                        "thumb_offset": 0
                    },
                    timeout=30.0
                )

                media_response.raise_for_status()
                media_data = media_response.json()

                if not media_data.get("id"):
                    raise Exception(f"Instagram media error: {media_data}")

                media_id = media_data["id"]

                # Paso 2: Publicar media
                publish_url = f"{RedSocial.INSTAGRAM.value['api_endpoint']}/{cred.user_id}/media_publish"

                publish_response = await client.post(
                    publish_url,
                    headers={"Authorization": f"Bearer {cred.access_token}"},
                    json={"creation_id": media_id},
                    timeout=30.0
                )

                publish_response.raise_for_status()
                publish_data = publish_response.json()

                if not publish_data.get("id"):
                    raise Exception(f"Instagram publish error: {publish_data}")

                resultado.exitoso = True
                resultado.id_post = publish_data["id"]
                resultado.url_post = f"https://www.instagram.com/p/{resultado.id_post}"
                resultado.metricas_iniciales = {"impressions": 0, "likes": 0, "comments": 0}

        except Exception as e:
            resultado.error = str(e)
            logger.error(f"Instagram error: {e}")

        return resultado

    async def _publicar_youtube(
        self,
        cred: CredencialesRed,
        config: ConfiguracionPublicacion,
        caption: str
    ) -> ResultadoPublicacion:
        """Publica en YouTube usando API real"""

        resultado = ResultadoPublicacion(red=RedSocial.YOUTUBE, exitoso=False)

        try:
            async with httpx.AsyncClient() as client:
                # Crear video en YouTube
                upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"

                with open(config.archivo_video_path, 'rb') as f:
                    files = {'file': f}
                    data = {
                        'part': 'snippet,status',
                        'snippet': json.dumps({
                            "title": config.titulo,
                            "description": caption,
                            "tags": config.hashtags.get("YouTube", []),
                            "categoryId": "24",  # Entertainment
                            "defaultLanguage": "es"
                        }),
                        'status': json.dumps({
                            "privacyStatus": "public",
                            "publishAt": (
                                config.horario_publicacion.isoformat()
                                if config.horario_publicacion
                                else None
                            )
                        })
                    }

                    upload_response = await client.post(
                        upload_url,
                        headers={"Authorization": f"Bearer {cred.access_token}"},
                        params={'uploadType': 'multipart'},
                        files=files,
                        data=data,
                        timeout=300.0
                    )

                    upload_response.raise_for_status()
                    upload_data = upload_response.json()

                    if not upload_data.get("id"):
                        raise Exception(f"YouTube upload error: {upload_data}")

                    resultado.exitoso = True
                    resultado.id_post = upload_data["id"]
                    resultado.url_post = f"https://www.youtube.com/watch?v={resultado.id_post}"
                    resultado.metricas_iniciales = {"views": 0, "likes": 0, "comments": 0}

        except Exception as e:
            resultado.error = str(e)
            logger.error(f"YouTube error: {e}")

        return resultado

    async def _publicar_facebook(
        self,
        cred: CredencialesRed,
        config: ConfiguracionPublicacion,
        caption: str
    ) -> ResultadoPublicacion:
        """Publica en Facebook usando API real"""

        resultado = ResultadoPublicacion(red=RedSocial.FACEBOOK, exitoso=False)

        try:
            async with httpx.AsyncClient() as client:
                # Publicar video en Facebook
                post_url = f"{RedSocial.FACEBOOK.value['api_endpoint']}/{cred.user_id}/videos"

                with open(config.archivo_video_path, 'rb') as f:
                    files = {'source': f}

                    post_response = await client.post(
                        post_url,
                        headers={"Authorization": f"Bearer {cred.access_token}"},
                        files=files,
                        data={
                            'description': caption,
                            'published': 'true' if not config.horario_publicacion else 'false',
                            'scheduled_publish_time': (
                                int(config.horario_publicacion.timestamp())
                                if config.horario_publicacion
                                else None
                            )
                        },
                        timeout=300.0
                    )

                    post_response.raise_for_status()
                    post_data = post_response.json()

                    if not post_data.get("id"):
                        raise Exception(f"Facebook publish error: {post_data}")

                    resultado.exitoso = True
                    resultado.id_post = post_data["id"]
                    resultado.url_post = f"https://www.facebook.com/watch/?v={resultado.id_post}"
                    resultado.metricas_iniciales = {"views": 0, "likes": 0, "comments": 0}

        except Exception as e:
            resultado.error = str(e)
            logger.error(f"Facebook error: {e}")

        return resultado

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de publicaciones"""
        if not self.historial_publicaciones:
            return {"total": 0, "exitosas": 0, "fallidas": 0}

        exitosas = sum(1 for p in self.historial_publicaciones if p.exitoso)
        fallidas = len(self.historial_publicaciones) - exitosas

        return {
            "total": len(self.historial_publicaciones),
            "exitosas": exitosas,
            "fallidas": fallidas,
            "tasa_exito": f"{(exitosas / len(self.historial_publicaciones) * 100):.1f}%",
            "historial": [
                {
                    "red": p.red.value['nombre'],
                    "exitoso": p.exitoso,
                    "id_post": p.id_post,
                    "url": p.url_post,
                    "error": p.error,
                    "timestamp": p.timestamp.isoformat()
                }
                for p in self.historial_publicaciones
            ]
        }


# Ejemplo de uso
async def ejemplo_uso():
    """Ejemplo de cómo usar el publicador profesional"""

    # Cargar credenciales (desde variables de entorno)
    credenciales = {}

    tiktok_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if tiktok_token:
        credenciales[RedSocial.TIKTOK] = CredencialesRed(
            red=RedSocial.TIKTOK,
            access_token=tiktok_token,
            user_id=os.getenv("TIKTOK_USER_ID", ""),
            username=os.getenv("TIKTOK_USERNAME", ""),
            cuenta_verificada=True
        )

    instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if instagram_token:
        credenciales[RedSocial.INSTAGRAM] = CredencialesRed(
            red=RedSocial.INSTAGRAM,
            access_token=instagram_token,
            user_id=os.getenv("INSTAGRAM_USER_ID", ""),
            username=os.getenv("INSTAGRAM_USERNAME", ""),
            cuenta_verificada=True
        )

    # Crear publicador
    async with PublicadorATFProfesional(credenciales) as publicador:
        # Configurar publicación
        config = ConfiguracionPublicacion(
            titulo="ATF Retrofit - Nuevo Bumper Deportivo",
            descripcion="Descubre nuestro nuevo bumper deportivo para Ford Mustang",
            archivo_video_path="C:\\Videos\\atf_demo.mp4",
            redes=[RedSocial.TIKTOK, RedSocial.INSTAGRAM],
            captions_personalizados={
                "TikTok": "🚗 Bumper deportivo de calidad premium #ATF #Retrofit",
                "Instagram": "Nuevo bumper disponible ahora 🔥"
            },
            hashtags={
                "TikTok": ["#ATF", "#Retrofit", "#Tuning"],
                "Instagram": ["#retrofit", "#tuning", "#autopartes"]
            }
        )

        # Publicar
        resultados = await publicador.publicar_multi_red(config)

        # Mostrar estadísticas
        stats = publicador.obtener_estadisticas()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(ejemplo_uso())
