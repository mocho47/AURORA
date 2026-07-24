#!/usr/bin/env python3
"""Escribe el panel maestro AURORA en TEMPLATES/panel-completo.html"""
from pathlib import Path

html = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AURORA — Panel Maestro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0b0d1a;color:#e2e8f0;display:flex;height:100vh;overflow:hidden}
/* SIDEBAR */
.sidebar{width:220px;background:#111827;border-right:1px solid #1e2a3a;display:flex;flex-direction:column;flex-shrink:0}
.logo{padding:22px 18px 18px;border-bottom:1px solid #1e2a3a;text-align:center}
.logo h1{font-size:22px;font-weight:800;background:linear-gradient(135deg,#7c3aed,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:2px}
.logo small{color:#6b7280;font-size:10px;letter-spacing:1px}
nav{flex:1;padding:12px 0;overflow-y:auto}
nav a{display:flex;align-items:center;gap:10px;padding:11px 18px;color:#9ca3af;font-size:13px;cursor:pointer;border-left:3px solid transparent;transition:all .2s;text-decoration:none}
nav a:hover,nav a.active{color:#e2e8f0;background:#1f2937;border-left-color:#7c3aed}
nav a span.icon{font-size:16px;width:20px;text-align:center}
.status-dot{width:8px;height:8px;border-radius:50%;margin-left:auto}
.dot-green{background:#22c55e;box-shadow:0 0 6px #22c55e}
.dot-red{background:#ef4444}
.dot-yellow{background:#f59e0b}
/* MAIN */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.topbar{background:#111827;border-bottom:1px solid #1e2a3a;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.topbar h2{font-size:16px;font-weight:600;color:#f1f5f9}
.topbar-right{display:flex;gap:12px;align-items:center}
.badge{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}
.badge-green{background:#052e16;color:#22c55e;border:1px solid #166534}
.badge-purple{background:#2e1065;color:#a78bfa;border:1px solid #4c1d95}
.content{flex:1;overflow-y:auto;padding:20px}
/* CARDS */
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.card{background:#111827;border:1px solid #1e2a3a;border-radius:10px;padding:18px}
.card h3{font-size:11px;text-transform:uppercase;color:#6b7280;letter-spacing:1px;margin-bottom:10px}
.card .val{font-size:28px;font-weight:700;color:#f1f5f9}
.card .sub{font-size:12px;color:#6b7280;margin-top:4px}
.card-full{grid-column:1/-1}
/* CHAT */
.chat-wrap{display:flex;flex-direction:column;height:460px}
.chat-msgs{flex:1;overflow-y:auto;padding:12px;background:#0b0d1a;border-radius:8px;border:1px solid #1e2a3a;display:flex;flex-direction:column;gap:10px;margin-bottom:12px}
.msg{max-width:80%;padding:10px 14px;border-radius:10px;font-size:13px;line-height:1.5}
.msg.user{align-self:flex-end;background:#4c1d95;color:#ede9fe;border-radius:10px 10px 2px 10px}
.msg.aurora{align-self:flex-start;background:#1f2937;color:#e2e8f0;border-radius:10px 10px 10px 2px}
.msg.aurora .motor-tag{font-size:10px;color:#7c3aed;margin-bottom:4px;font-weight:600}
.chat-input-row{display:flex;gap:8px}
.chat-input{flex:1;background:#1f2937;border:1px solid #374151;border-radius:8px;padding:10px 14px;color:#e2e8f0;font-size:13px;outline:none;resize:none}
.chat-input:focus{border-color:#7c3aed}
.btn{padding:10px 18px;border-radius:8px;border:none;cursor:pointer;font-size:13px;font-weight:600;transition:all .2s}
.btn-purple{background:#7c3aed;color:#fff}
.btn-purple:hover{background:#6d28d9}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-green{background:#065f46;color:#6ee7b7}
.btn-red{background:#7f1d1d;color:#fca5a5}
/* TABLE */
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:8px 10px;color:#6b7280;border-bottom:1px solid #1e2a3a;font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:.5px}
td{padding:9px 10px;border-bottom:1px solid #111827;color:#d1d5db}
tr:hover td{background:#1f2937}
.pill{padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600}
.pill-green{background:#052e16;color:#22c55e}
.pill-yellow{background:#451a03;color:#fbbf24}
.pill-red{background:#450a0a;color:#f87171}
.pill-blue{background:#0c1a3a;color:#60a5fa}
/* BUS */
.bus-items{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.bus-item{padding:5px 12px;background:#1f2937;border:1px solid #374151;border-radius:20px;font-size:11px;color:#9ca3af;display:flex;align-items:center;gap:6px}
.bus-item.registrado{border-color:#22c55e;color:#22c55e}
/* SECTION */
section{display:none}
section.active{display:block}
.refresh-btn{font-size:10px;padding:4px 8px;background:#1f2937;border:1px solid #374151;color:#9ca3af;border-radius:6px;cursor:pointer;margin-left:auto}
.section-header{display:flex;align-items:center;margin-bottom:16px;gap:10px}
.section-header h2{font-size:18px;font-weight:700;color:#f1f5f9}
/* SCROLLBAR */
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:#111827}::-webkit-scrollbar-thumb{background:#374151;border-radius:2px}
</style>
</head>
<body>

<div class="sidebar">
  <div class="logo">
    <h1>AURORA</h1>
    <small>v3 · SISTEMA MAESTRO</small>
  </div>
  <nav>
    <a class="active" onclick="go('dash',this)"><span class="icon">◈</span> Dashboard<span class="status-dot dot-green" id="sys-dot"></span></a>
    <a onclick="go('chat',this)"><span class="icon">◉</span> Chat AURORA</a>
    <a onclick="go('crm',this)"><span class="icon">◎</span> CRM · Leads</a>
    <a onclick="go('pedidos',this)"><span class="icon">◐</span> Pedidos</a>
    <a onclick="go('bus',this)"><span class="icon">◈</span> Bus Neuronal</a>
    <a onclick="go('memoria',this)"><span class="icon">◉</span> Memoria</a>
  </nav>
</div>

<div class="main">
  <div class="topbar">
    <h2 id="page-title">Dashboard</h2>
    <div class="topbar-right">
      <span class="badge badge-green" id="sys-status">● CARGANDO...</span>
      <span class="badge badge-purple" id="motores-badge">-- motores</span>
    </div>
  </div>

  <div class="content">

    <!-- DASHBOARD -->
    <section id="dash" class="active">
      <div class="grid-4">
        <div class="card">
          <h3>Sistema</h3>
          <div class="val" id="d-status">--</div>
          <div class="sub" id="d-ts">--</div>
        </div>
        <div class="card">
          <h3>Motores activos</h3>
          <div class="val" id="d-motores">--</div>
          <div class="sub">en bus neuronal</div>
        </div>
        <div class="card">
          <h3>Leads totales</h3>
          <div class="val" id="d-leads">--</div>
          <div class="sub">en ORACLE CRM</div>
        </div>
        <div class="card">
          <h3>Pedidos activos</h3>
          <div class="val" id="d-pedidos">--</div>
          <div class="sub">en pedidos.db</div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <h3>Resumen CRM · ATF</h3>
          <div id="crm-resumen" style="font-size:13px;line-height:1.8;color:#9ca3af">Cargando...</div>
        </div>
        <div class="card">
          <h3>Memoria cognitiva</h3>
          <div id="mem-resumen" style="font-size:13px;line-height:1.8;color:#9ca3af">Cargando...</div>
        </div>
      </div>
    </section>

    <!-- CHAT -->
    <section id="chat">
      <div class="section-header">
        <h2>Chat con AURORA</h2>
        <button class="refresh-btn" onclick="limpiarChat()">Limpiar</button>
      </div>
      <div class="card chat-wrap">
        <div class="chat-msgs" id="chat-msgs">
          <div class="msg aurora"><div class="motor-tag">AURORA · Consciencia</div>Listo para operar. ¿En qué te ayudo hoy?</div>
        </div>
        <div class="chat-input-row">
          <textarea class="chat-input" id="chat-in" rows="2" placeholder="Escribe tu mensaje... (Enter = enviar)"></textarea>
          <button class="btn btn-purple" onclick="enviarChat()">Enviar</button>
        </div>
      </div>
    </section>

    <!-- CRM -->
    <section id="crm">
      <div class="section-header">
        <h2>CRM · Leads</h2>
        <select id="lead-filtro" onchange="cargarLeads()" style="background:#1f2937;border:1px solid #374151;color:#e2e8f0;padding:5px 8px;border-radius:6px;font-size:12px">
          <option value="">Todos</option>
          <option value="nuevo">Nuevos</option>
          <option value="contactado">Contactados</option>
          <option value="cotizado">Cotizados</option>
          <option value="ganado">Ganados</option>
          <option value="perdido">Perdidos</option>
        </select>
        <button class="refresh-btn" onclick="cargarLeads()">↻ Actualizar</button>
      </div>
      <div class="card">
        <div id="leads-tabla">Cargando leads...</div>
      </div>
    </section>

    <!-- PEDIDOS -->
    <section id="pedidos">
      <div class="section-header">
        <h2>Pedidos · FORJA</h2>
        <button class="refresh-btn" onclick="cargarPedidos()">↻ Actualizar</button>
      </div>
      <div class="card">
        <div id="pedidos-tabla">Cargando pedidos...</div>
      </div>
    </section>

    <!-- BUS NEURONAL -->
    <section id="bus">
      <div class="section-header">
        <h2>Bus Neuronal</h2>
        <button class="refresh-btn" onclick="cargarBus()">↻ Actualizar</button>
      </div>
      <div class="card" style="margin-bottom:14px">
        <h3>Estado del despachador</h3>
        <div id="bus-estado" style="font-size:13px;margin-top:8px;color:#9ca3af">Cargando...</div>
      </div>
      <div class="card">
        <h3>Motores registrados</h3>
        <div class="bus-items" id="bus-motores">Cargando...</div>
      </div>
    </section>

    <!-- MEMORIA -->
    <section id="memoria">
      <div class="section-header">
        <h2>Memoria Cognitiva</h2>
        <button class="refresh-btn" onclick="cargarMemoria()">↻ Actualizar</button>
      </div>
      <div class="grid-2">
        <div class="card">
          <h3>Estadísticas</h3>
          <div id="mem-stats" style="font-size:13px;line-height:2;color:#9ca3af;margin-top:8px">Cargando...</div>
        </div>
        <div class="card">
          <h3>Semántica reciente (patrones aprendidos)</h3>
          <div id="mem-semantica" style="font-size:12px;line-height:1.8;color:#9ca3af;margin-top:8px">Cargando...</div>
        </div>
      </div>
    </section>

  </div><!-- /content -->
</div><!-- /main -->

<script>
const API = '';

// ── Navegación ─────────────────────────────────────────────────────
function go(id, el) {
  document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
  document.getElementById('page-title').textContent = el.textContent.trim();
  const loaders = {dash: cargarDash, crm: cargarLeads, pedidos: cargarPedidos, bus: cargarBus, memoria: cargarMemoria};
  if (loaders[id]) loaders[id]();
}

// ── Fetch helper ────────────────────────────────────────────────────
async function api(path, opts) {
  try {
    const r = await fetch(API + path, opts);
    return await r.json();
  } catch(e) {
    return {error: e.message};
  }
}

// ── Estado de color por estado ──────────────────────────────────────
function pill(estado) {
  const map = {nuevo:'pill-blue',contactado:'pill-yellow',cotizado:'pill-yellow',ganado:'pill-green',perdido:'pill-red',pendiente:'pill-yellow',confirmado:'pill-green',entregado:'pill-green',en_proceso:'pill-yellow'};
  return `<span class="pill ${map[estado]||'pill-blue'}">${estado}</span>`;
}

// ── DASHBOARD ───────────────────────────────────────────────────────
async function cargarDash() {
  const [health, status, leads, pedidos, crm, mem] = await Promise.all([
    api('/health'), api('/status'), api('/oracle/leads?limite=1'),
    api('/pedidos/lista'), api('/oracle/resumen'), api('/memoria/resumen')
  ]);

  document.getElementById('d-status').textContent = health.error ? 'ERROR' : 'OPERATIVO';
  document.getElementById('d-ts').textContent = health.timestamp ? new Date(health.timestamp).toLocaleString('es-MX') : '--';
  document.getElementById('d-motores').textContent = status.motores_activos || '--';
  document.getElementById('d-leads').textContent = leads.total !== undefined ? leads.total : '--';
  document.getElementById('d-pedidos').textContent = pedidos.total !== undefined ? pedidos.total : '--';
  document.getElementById('sys-status').textContent = health.error ? '● ERROR' : '● OPERATIVO';
  document.getElementById('sys-status').className = 'badge ' + (health.error ? 'badge-red' : 'badge-green');
  document.getElementById('sys-dot').className = 'status-dot ' + (health.error ? 'dot-red' : 'dot-green');
  document.getElementById('motores-badge').textContent = (status.motores_activos || '--') + ' motores';

  // CRM resumen
  if (crm && !crm.error) {
    const html = Object.entries(crm).filter(([k]) => !['error'].includes(k))
      .map(([k,v]) => `<div><b style="color:#f1f5f9">${k}</b>: ${JSON.stringify(v)}</div>`).join('');
    document.getElementById('crm-resumen').innerHTML = html || 'Sin datos';
  }

  // Memoria resumen
  if (mem && !mem.error) {
    let html = `<div><b style="color:#f1f5f9">Episodios:</b> ${mem.episodios_total || 0}</div>`;
    if (mem.semantica_reciente?.length) {
      html += `<div style="margin-top:8px;color:#7c3aed;font-weight:600;font-size:10px">PATRONES RECIENTES</div>`;
      mem.semantica_reciente.slice(0,3).forEach(k => {
        html += `<div style="font-size:11px;margin-top:4px"><b style="color:#a78bfa">${k.tema||''}</b>: ${k.conocimiento?.slice(0,60)||''}...</div>`;
      });
    }
    document.getElementById('mem-resumen').innerHTML = html;
  }
}

// ── CHAT ────────────────────────────────────────────────────────────
const chatIn = () => document.getElementById('chat-in');
const chatMsgs = () => document.getElementById('chat-msgs');

document.addEventListener('DOMContentLoaded', () => {
  chatIn().addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviarChat(); }
  });
  cargarDash();
});

function addMsg(texto, tipo, motor) {
  const div = document.createElement('div');
  div.className = 'msg ' + tipo;
  if (tipo === 'aurora') div.innerHTML = `<div class="motor-tag">${motor || 'AURORA'}</div>${texto.replace(/\n/g,'<br>')}`;
  else div.textContent = texto;
  chatMsgs().appendChild(div);
  chatMsgs().scrollTop = chatMsgs().scrollHeight;
}

async function enviarChat() {
  const msg = chatIn().value.trim();
  if (!msg) return;
  chatIn().value = '';
  addMsg(msg, 'user');
  const loading = document.createElement('div');
  loading.className = 'msg aurora'; loading.innerHTML = '<div class="motor-tag">AURORA</div>Procesando...';
  chatMsgs().appendChild(loading);
  chatMsgs().scrollTop = chatMsgs().scrollHeight;

  const r = await api('/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({mensaje: msg, user_id: 'anuar', canal: 'panel'})
  });

  chatMsgs().removeChild(loading);
  if (r.error) addMsg('Error: ' + r.error, 'aurora', 'ERROR');
  else addMsg(r.respuesta || r.error || 'Sin respuesta', 'aurora',
    (r.motores_usados?.join(' + ') || 'consciencia') + ' · ' + (r.temperatura_lead||'frio') + ' · ' + (r.duracion_ms||'--') + 'ms');
}

function limpiarChat() {
  chatMsgs().innerHTML = '<div class="msg aurora"><div class="motor-tag">AURORA · Consciencia</div>Chat limpiado. ¿En qué te ayudo?</div>';
}

// ── CRM LEADS ───────────────────────────────────────────────────────
async function cargarLeads() {
  const estado = document.getElementById('lead-filtro')?.value || '';
  const url = '/oracle/leads' + (estado ? '?estado=' + estado : '');
  const data = await api(url);
  const el = document.getElementById('leads-tabla');
  if (data.error || !data.leads) { el.innerHTML = '<div style="color:#ef4444;padding:10px">'+( data.error||'Sin datos')+'</div>'; return; }
  if (!data.leads.length) { el.innerHTML = '<div style="color:#6b7280;padding:10px">Sin leads con este filtro.</div>'; return; }
  el.innerHTML = `<table>
    <tr><th>#</th><th>Nombre</th><th>Teléfono</th><th>Negocio</th><th>Vehículo</th><th>Estado</th><th>Creado</th></tr>
    ${data.leads.map(l => `<tr>
      <td style="color:#6b7280">${l.id}</td>
      <td style="font-weight:600;color:#f1f5f9">${l.nombre||'--'}</td>
      <td>${l.telefono||'--'}</td>
      <td>${(l.negocio||'atf').toUpperCase()}</td>
      <td>${l.vehiculo||'--'}</td>
      <td>${pill(l.estado||'nuevo')}</td>
      <td style="color:#6b7280;font-size:11px">${(l.creado||'').slice(0,10)}</td>
    </tr>`).join('')}
  </table>`;
}

// ── PEDIDOS ─────────────────────────────────────────────────────────
async function cargarPedidos() {
  const data = await api('/pedidos/lista');
  const el = document.getElementById('pedidos-tabla');
  if (data.error || !data.pedidos) { el.innerHTML = '<div style="color:#ef4444;padding:10px">'+(data.error||'Sin datos')+'</div>'; return; }
  if (!data.pedidos.length) { el.innerHTML = '<div style="color:#6b7280;padding:10px">Sin pedidos registrados.</div>'; return; }
  el.innerHTML = `<table>
    <tr><th>ID</th><th>Negocio</th><th>Cliente</th><th>Producto</th><th>Precio</th><th>Estado</th><th>Creado</th></tr>
    ${data.pedidos.map(p => `<tr>
      <td style="color:#7c3aed;font-size:11px;font-weight:600">${p.id||'--'}</td>
      <td>${(p.negocio||'').toUpperCase()}</td>
      <td style="font-weight:600;color:#f1f5f9">${p.cliente||'--'}</td>
      <td>${p.producto||'--'}</td>
      <td style="color:#22c55e">$${(p.precio||0).toLocaleString()}</td>
      <td>${pill(p.estado||'pendiente')}</td>
      <td style="color:#6b7280;font-size:11px">${(p.creado||'').slice(0,10)}</td>
    </tr>`).join('')}
  </table>`;
}

// ── BUS NEURONAL ─────────────────────────────────────────────────────
async function cargarBus() {
  const data = await api('/bus/estado');
  const el = document.getElementById('bus-estado');
  const em = document.getElementById('bus-motores');
  if (data.error) { el.textContent = 'Error: ' + data.error; return; }
  el.innerHTML = `
    <div><b style="color:#f1f5f9">Despachador:</b> ${data.despachador_activo ? '<span style="color:#22c55e">ACTIVO</span>' : '<span style="color:#ef4444">INACTIVO</span>'}</div>
    <div><b style="color:#f1f5f9">Cola de mensajes:</b> ${data.mensajes_en_cola ?? '--'}</div>
    <div><b style="color:#f1f5f9">Peticiones pendientes:</b> ${data.peticiones_pendientes ?? '--'}</div>
    <div><b style="color:#f1f5f9">Suscripciones totales:</b> ${data.total_suscripciones ?? '--'}</div>
  `;
  const motores = data.motores_registrados || [];
  em.innerHTML = motores.length
    ? motores.map(m => `<div class="bus-item registrado">● ${m}</div>`).join('')
    : '<div style="color:#6b7280">Ningún motor registrado aún (iniciar run_aurora.py)</div>';
}

// ── MEMORIA ──────────────────────────────────────────────────────────
async function cargarMemoria() {
  const data = await api('/memoria/resumen');
  const es = document.getElementById('mem-stats');
  const sem = document.getElementById('mem-semantica');
  if (data.error) { es.textContent = 'Error: ' + data.error; return; }
  es.innerHTML = `
    <div><b style="color:#f1f5f9">Episodios registrados:</b> ${data.episodios_total ?? '--'}</div>
  `;
  const s = data.semantica_reciente || [];
  if (!s.length) { sem.textContent = 'Sin patrones semánticos aún.'; return; }
  sem.innerHTML = s.map(k => `
    <div style="margin-bottom:10px;padding:8px;background:#0b0d1a;border-radius:6px;border-left:2px solid #7c3aed">
      <div style="color:#a78bfa;font-weight:600;font-size:11px">${k.tema||''} · ${k.patron||''}</div>
      <div style="color:#d1d5db;font-size:12px;margin-top:3px">${k.conocimiento||''}</div>
      <div style="color:#6b7280;font-size:10px;margin-top:3px">confianza ${((k.confianza||0)*100).toFixed(0)}%</div>
    </div>
  `).join('');
}
</script>
</body>
</html>
"""

ruta = Path(__file__).parent.parent / "TEMPLATES" / "panel-completo.html"
with open(ruta, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK  panel-completo.html  ({ruta.stat().st_size:,} bytes)")
