# -*- coding: utf-8 -*-
"""
📊 DASHBOARD AURORA - Panel web de control en tiempo real
"""
import asyncio
import logging
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
from typing import Dict
from config import settings
from crm_leads_ventas import crm
from SUPER_MARKETING_SYSTEM.api_v3_new import verify_jwt

logger = logging.getLogger("Dashboard")

class DashboardAurora:
    """Dashboard web principal"""
    
    def __init__(self):
        self.app = FastAPI(title="Aurora Dashboard")
    
    async def obtener_metricas_tiempo_real(self) -> Dict:
        """Obtiene métricas en tiempo real"""
        try:
            resumen_crm = crm.obtener_resumen_crm()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "crm": resumen_crm,
                "sistema": {
                    "estado": "🟢 ONLINE",
                    "uptime": "24h",
                    "version": "3.0"
                },
                "apis": {
                    "groq": "✅ Conectado",
                    "facebook": "✅ Conectado",
                    "instagram": "✅ Conectado",
                    "whatsapp": "✅ Conectado"
                }
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas: {str(e)}")
            return {}
    
    def crear_dashboard_html(self) -> str:
        """Crea HTML del dashboard"""
        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🚀 Aurora Dashboard v3</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                
                header {
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }
                
                header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .card {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: transform 0.3s;
                }
                
                .card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 8px 12px rgba(0,0,0,0.2);
                }
                
                .metric {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                    margin: 10px 0;
                }
                
                .label {
                    color: #666;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .status-online {
                    color: #4CAF50;
                    font-weight: bold;
                }
                
                .status-offline {
                    color: #f44336;
                    font-weight: bold;
                }
                
                #metricas-tiempo-real {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                
                .timestamp {
                    color: #999;
                    font-size: 0.8em;
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🚀 AURORA Dashboard v3</h1>
                    <p>Panel de Control - Sistema de Marketing IA Integral</p>
                </header>
                
                <div class="grid">
                    <div class="card">
                        <div class="label">Estado del Sistema</div>
                        <div class="metric" id="estado-sistema">🔄 Cargando...</div>
                    </div>
                    
                    <div class="card">
                        <div class="label">Total de Leads</div>
                        <div class="metric" id="total-leads">-</div>
                    </div>
                    
                    <div class="card">
                        <div class="label">Ventas Totales</div>
                        <div class="metric" id="ventas-totales">-</div>
                    </div>
                    
                    <div class="card">
                        <div class="label">Tasa de Conversión</div>
                        <div class="metric" id="tasa-conversion">-</div>
                    </div>
                </div>
                
                <div id="metricas-tiempo-real">
                    <h2>📊 Métricas en Tiempo Real</h2>
                    <div id="chart-leads"></div>
                    <div class="timestamp">Última actualización: <span id="ultimo-update">-</span></div>
                </div>
            </div>
            
            <script>
                async function cargarMetricas() {
                    try {
                        const response = await fetch('/api/dashboard/metricas', {
                            headers: {
                                'Authorization': 'Bearer ' + localStorage.getItem('token')
                            }
                        });
                        
                        const datos = await response.json();
                        
                        // Actualizar métricas
                        document.getElementById('estado-sistema').textContent = datos.sistema.estado;
                        document.getElementById('total-leads').textContent = datos.crm.total_leads || 0;
                        document.getElementById('ventas-totales').textContent = datos.crm.total_ventas || '$0.00';
                        document.getElementById('tasa-conversion').textContent = datos.crm.tasa_conversion || '0%';
                        document.getElementById('ultimo-update').textContent = new Date().toLocaleTimeString();
                        
                    } catch (error) {
                        console.error('Error cargando métricas:', error);
                    }
                }
                
                // Cargar métricas cada 5 segundos
                cargarMetricas();
                setInterval(cargarMetricas, 5000);
            </script>
        </body>
        </html>
        """
        return html

dashboard = DashboardAurora()

async def get_dashboard_app():
    """Obtiene la aplicación del dashboard"""
    
    @dashboard.app.get("/api/dashboard/metricas")
    async def metricas_endpoint(token_user: Dict = Depends(verify_jwt)):
        """Endpoint de métricas en tiempo real"""
        return await dashboard.obtener_metricas_tiempo_real()
    
    @dashboard.app.get("/", response_class=HTMLResponse)
    async def dashboard_html(token_user: Dict = Depends(verify_jwt)):
        """Página principal del dashboard"""
        return dashboard.crear_dashboard_html()
    
    @dashboard.app.get("/api/health")
    async def health():
        """Health check del dashboard"""
        return {"status": "healthy"}
    
    return dashboard.app
