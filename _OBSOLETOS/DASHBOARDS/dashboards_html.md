# 📊 DASHBOARDS AURORA - Especificación HTML

## DASHBOARD TEEN (Adolescente)

```html
<!-- MI ESPACIO TEEN -->
<div class="dashboard-teen">
  <div class="card-hero">
    <h1>🧠 Mi Espacio</h1>
    <p id="nombre-teen">Hola [Nombre]</p>
  </div>

  <div class="grid-2">
    <!-- FORTALEZAS -->
    <div class="card">
      <h3>💪 Mis Fortalezas</h3>
      <div id="fortalezas-detectadas">
        <div class="badge">Creatividad</div>
        <div class="badge">Empatía</div>
        <div class="badge">Liderazgo</div>
      </div>
    </div>

    <!-- ESTADO EMOCIONAL -->
    <div class="card">
      <h3>😌 Cómo me siento hoy</h3>
      <div id="estado-emocional">
        <button onclick="reportarEstado('bien')">✅ Bien</button>
        <button onclick="reportarEstado('normal')">😐 Normal</button>
        <button onclick="reportarEstado('mal')">😟 Mal</button>
      </div>
    </div>
  </div>

  <!-- HERRAMIENTAS RÁPIDAS -->
  <div class="card">
    <h3>😌 Herramientas si te sientes abrumado</h3>
    <div class="grid-3">
      <button onclick="herramienta('respiracion')">🫁 Respirar (5 min)</button>
      <button onclick="herramienta('grounding')">🌍 Grounding (3 min)</button>
      <button onclick="herramienta('movimiento')">🏃 Movimiento</button>
    </div>
  </div>

  <!-- REGULARIZACIÓN -->
  <div class="card">
    <h3>📚 Tu Regularización</h3>
    <div id="materias-regularizacion">
      <div class="materia-bien">✅ Español: Excelente</div>
      <div class="materia-normal">😐 Matemáticas: Regular</div>
      <div class="materia-alerta">⚠️ Química: Necesita ayuda</div>
    </div>
  </div>

  <!-- PRÓXIMOS PASOS -->
  <div class="card">
    <h3>🎯 Próximo Paso</h3>
    <p>Hablar con profesor de Química para extra sesión</p>
    <button onclick="agendar()">📅 Agendar</button>
  </div>
</div>
```

---

## DASHBOARD MAESTRO (Educación)

```html
<!-- ESTADO DEL AULA MAESTRO -->
<div class="dashboard-maestro">
  <div class="header-maestro">
    <h1>📊 Estado del Aula - [Clase, Hora]</h1>
    <div class="stats">
      <div class="stat">Asistencia: 28/30</div>
      <div class="stat">Tareas: 26/30 entregadas</div>
      <div class="stat">Clima: 🟢 Positivo</div>
    </div>
  </div>

  <!-- DINÁMICAS DISPONIBLES HOY -->
  <div class="card">
    <h3>🎲 Dinámicas Sugeridas Hoy</h3>
    <div class="dinamica-item">
      <h4>Reto de 72 horas</h4>
      <p>Tema: Aplicar concepto en vida real</p>
      <button onclick="lanzarDinamica('reto72')">🚀 Lanzar</button>
    </div>
    <div class="dinamica-item">
      <h4>Experto por un día</h4>
      <p>María (buena en análisis) → Enseña a grupo</p>
      <button onclick="lanzarDinamica('experto')">🚀 Lanzar</button>
    </div>
    <div class="dinamica-item">
      <h4>Debate Estructurado</h4>
      <p>Tema: ¿Tecnología ayuda o perjudica?</p>
      <button onclick="lanzarDinamica('debate')">🚀 Lanzar</button>
    </div>
  </div>

  <!-- ALERTAS DE RIESGO -->
  <div class="card alerta-riesgo">
    <h3>🚨 Alertas</h3>
    <div class="alerta">
      <strong>Juan:</strong> No entregó 3 tareas + ausencias aumentadas
      <button onclick="intervenir('juan')">Intervenir</button>
    </div>
    <div class="alerta">
      <strong>Ana:</strong> Signos de ansiedad en círculo de confianza
      <button onclick="intervenir('ana')">Intervenir</button>
    </div>
  </div>

  <!-- RECURSOS -->
  <div class="card">
    <h3>📚 Recursos - Hoy es sobre [Tema]</h3>
    <ul>
      <li>📖 Fragmento libro texto (SEP)</li>
      <li>🎬 Video explicativo 8 min</li>
      <li>📋 Ejercicio práctico</li>
      <li>🔗 Vinculación a vida real</li>
    </ul>
  </div>

  <!-- REPORTES -->
  <div class="card">
    <h3>📋 Reportes Auto-generados</h3>
    <button onclick="generarReporte('semanal')">Reporte Semanal</button>
    <button onclick="generarReporte('alumnos')">Por Alumno</button>
    <button onclick="generarReporte('dinamicas')">Dinámicas</button>
  </div>
</div>
```

---

## DASHBOARD PADRE (Familia)

```html
<!-- ESCUELA PARA PADRES - INVISIBLEMENTE PERSONALIZADA -->
<div class="dashboard-padre">
  <h1>👨‍👩‍👧 Panel Familia</h1>

  <!-- NOTA: Padre NO ve formularios ni cuestionarios -->
  <!-- Solo opciones útiles, automáticamente seleccionadas por AURORA -->

  <div class="card">
    <h3>💡 Opción de Hoy para Ti</h3>
    
    <!-- AURORA detectó que hay ansiedad en tu hijo -->
    <div class="opcion-padre">
      <h4>📻 Audio: "Entender la ansiedad adolescente" (10 min)</h4>
      <p>Qué es normal a esta edad, cuándo es preocupante, cómo ayudar</p>
      <button onclick="reproducir('audio-ansiedad')">▶️ Escuchar</button>
    </div>

    <p style="text-align: center; color: #888; margin: 20px 0;">O bien...</p>

    <div class="opcion-padre">
      <h4>✉️ Email: "Comunicación sin culpa" (lectura 15 min)</h4>
      <p>Preguntas que abren diálogo, cómo escuchar realmente</p>
      <button onclick="leer('email-comunicacion')">📧 Leer</button>
    </div>

    <p style="text-align: center; color: #999; font-size: 12px;">
      Sin obligación. Solo información útil.<br/>
      No es un diagnóstico de tu hijo. Es apoyo para ti.
    </p>
  </div>

  <!-- COMUNICACIÓN CON ESCUELA -->
  <div class="card">
    <h3>💬 Comunicación con la Escuela</h3>
    <p>Última comunicación: Hace 3 días</p>
    <button onclick="verMensajes()">Ver mensajes</button>
    <button onclick="enviarMensaje()">Enviar mensaje</button>
  </div>

  <!-- NINGÚN JUICIO -->
  <div class="card" style="background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22c55e;">
    <p style="color: #22c55e;">
      ✓ Eres buen padre/madre por estar aquí<br/>
      ✓ No hay respuestas perfectas<br/>
      ✓ Tu conexión con tu hijo/a es lo más importante
    </p>
  </div>
</div>
```

---

## DASHBOARD ADMIN (Sistema)

```html
<!-- ADMIN DASHBOARD -->
<div class="dashboard-admin">
  <h1>⚙️ Control Administrativo</h1>

  <div class="grid-3">
    <div class="stat-card">
      <h3>👥 Usuarios Activos</h3>
      <div class="big-number">342</div>
      <div class="trend">↑ 12% esta semana</div>
    </div>

    <div class="stat-card">
      <h3>💬 Interacciones</h3>
      <div class="big-number">2,847</div>
      <div class="trend">Promedio 8.3 por usuario</div>
    </div>

    <div class="stat-card">
      <h3>🚨 Crisis Detectadas</h3>
      <div class="big-number">3</div>
      <div class="trend">0 críticas sin intervención</div>
    </div>
  </div>

  <!-- FINANZAS (si aplica) -->
  <div class="card">
    <h3>💰 Finanzas</h3>
    <table>
      <tr><td>Ingresos mes:</td><td>$15,340</td></tr>
      <tr><td>Gastos:</td><td>$2,100</td></tr>
      <tr><td>Ganancia neta:</td><td>$13,240</td></tr>
      <tr><td>Margen promedio:</td><td>47%</td></tr>
    </table>
  </div>

  <!-- SISTEMA HEALTH -->
  <div class="card">
    <h3>🏥 Salud del Sistema</h3>
    <div class="health-item">✅ Librerías: 16/16 operativas</div>
    <div class="health-item">✅ Dinámicas: 6/6 funcionales</div>
    <div class="health-item">✅ Crisis protocol: Activo</div>
    <div class="health-item">✅ Uptime: 99.8%</div>
  </div>

  <!-- LOGS -->
  <div class="card">
    <h3>📋 Eventos Recientes</h3>
    <div class="log-entry">18:45 - Crisis level 4 detectada, alerta enviada a padres</div>
    <div class="log-entry">18:32 - Dinámica "Experto por un día" lanzada en Aula 2B</div>
    <div class="log-entry">18:15 - Teen finalizó técnica de regulación (éxito)</div>
  </div>
</div>
```

---

## ESTILOS COMPARTIDOS

```css
.dashboard-teen, .dashboard-maestro, .dashboard-padre, .dashboard-admin {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  background: #1a1a3a;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }

.badge {
  display: inline-block;
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
  padding: 8px 16px;
  border-radius: 20px;
  margin: 5px;
  font-size: 13px;
}

.big-number {
  font-size: 36px;
  font-weight: bold;
  color: #667eea;
  margin: 10px 0;
}

.trend {
  font-size: 12px;
  color: #888;
}

.alerta-riesgo { border-left: 3px solid #ff6b6b; }
.alerta { background: rgba(255, 107, 107, 0.1); padding: 12px; margin: 10px 0; border-radius: 6px; }

button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
```

---

## PRÓXIMO PASO

Integrar estos dashboards al panel.html existente con:
- Detectores de rol automáticos
- Datos en tiempo real
- Actualizaciones dinámicas
- Personalización extrema
