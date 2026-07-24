# 🌟 AURORA v2 - GUÍA DE INICIO RÁPIDO

## ¿QUÉ ES AURORA?

**AURORA** es un sistema inteligente, sin censura, que acompaña a:
- **Adolescentes** con psicología real (sin imposición)
- **Maestros** con dinámicas educativas
- **Padres** con escuela para padres
- **Vendedores** con cotizador automático
- **Admins** con dashboards

---

## ⚡ INICIO EN 30 SEGUNDOS

### Opción 1: PowerShell
```powershell
Set-Location "C:\AURORA\CORE"
python servidor_aurora.py
```

### Opción 2: CMD
```cmd
cd C:\AURORA\CORE
python servidor_aurora.py
```

### Opción 3: Doble-click (Próximamente)
```
C:\AURORA\LANZAR_AURORA.bat
```

**Resultado:**
```
AURORA v2.0 - SERVIDOR PROFESIONAL INICIADO
Panel:    http://localhost:8000/panel
API:      http://localhost:8000/api/
```

Abre tu navegador → `http://localhost:8000/panel`

---

## 🎯 CARACTERÍSTICAS PRINCIPALES

### 1. Chat Inteligente (Sin Genérico)
```
Usuario: "Estoy muy estresado"
AURORA: "Entiendo... aquí técnica 4-4-4..."
```

**Detecta automáticamente:**
- Estrés → Herramientas de regulación
- Fracaso → Perspectiva de resiliencia  
- Soledad → Acompañamiento
- Identidad → Exploración segura
- Relaciones → Comunicación
- Sexualidad → Info sin tabú

### 2. Crisis Protocol (Automático)
**5 niveles de detección:**
```
Normal (1)
  ↓ (presión detectada)
Estresado (2) → Técnica 4-4-4
  ↓ (ansiedad detectada)
Ansioso (3) → Soporte intenso
  ↓ (autolesión/daño)
Riesgo (4) → ALERTA SILENCIOSA a adultos
  ↓ (intento suicidio)
Crítico (5) → 911 INMEDIATO
```

El sistema detecta todo automáticamente sin que el usuario lo sepa.

### 3. Cotizador Real
```
Vendedor abre panel
Selecciona: Servilletero × 100
AURORA calcula: Costo + Margen + Venta
Retorna: Cotización exacta
```

### 4. 6 Roles Simultáneos
- 🧠 Adolescente
- 👨‍🏫 Maestro  
- 👨‍👩‍👧 Padre
- 💼 Vendedor
- ⚙️ Admin
- 📊 Generales

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
C:\AURORA\
├─ CORE\
│  ├─ servidor_aurora.py       ← MAIN (ejecutable)
│  ├─ aurora_core.py           ← Orquestador
│  ├─ aurora_db.py             ← Base de datos
│  ├─ aurora_crisis.py          ← Crisis protocol
│  ├─ aurora_sdk_manager.py    ← Multi-SDK
│  └─ config.py                ← Configuración
│
├─ panel.html                   ← Interfaz web
├─ aurora.db                    ← Base de datos (auto-creada)
├─ LANZAR_AURORA.bat           ← Launcher Windows
├─ LANZAR_AURORA.ps1           ← Launcher PowerShell
│
├─ DOCUMENTACIÓN\
│  ├─ ARQUITECTURA_PROFESIONAL.md
│  ├─ RESUMEN_CONSTRUCCION_PROFESIONAL.md
│  ├─ GOAL_DESARROLLO_HUMANO_TEENS.md
│  ├─ PLAN_ECOSISTEMA_EDUCATIVO.md
│  └─ CATALOGO_FINAL_INTEGRADO.md
```

---

## 🔌 CONFIGURACIÓN (Opcional)

### Variables de Entorno
```bash
# Opcional - Para mejor performance
set ANTHROPIC_API_KEY=tu_clave_aqui
set GROQ_API_KEY=tu_clave_aqui
set OLLAMA_URL=http://localhost:11434
```

**Sin configurar:** Fallback automático a Ollama local

---

## 📝 EJEMPLOS DE USO

### Ejemplo 1: Adolescente Estresado
```
1. Abre http://localhost:8000/panel
2. Selecciona "Adolescente"
3. Abre Chat
4. Escribe: "Estoy muy estresado por examen mañana"
5. AURORA: Retorna técnica 4-4-4 + validación
```

### Ejemplo 2: Vendedor Cotiza
```
1. Selecciona "Vendedor"
2. Abre Cotizador
3. Selecciona: Servilletero × 100
4. AURORA: Calcula precio exacto
5. Copia al cliente
```

### Ejemplo 3: Maestro Lanza Dinámica
```
1. Selecciona "Maestro"
2. Ve: "Reto de 72 horas"
3. Hace clic: "Lanzar"
4. AURORA: Crea grupos MIXTOS
5. Monitorea enganche automáticamente
```

---

## 🧪 TEST RÁPIDO

### Verificar que está vivo
```bash
curl http://localhost:8000/health
```

### Chat real
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje":"Hola AURORA","rol":"teen","user_id":"test001"}'
```

### Cotizar producto
```bash
curl -X POST http://localhost:8000/api/cotizar \
  -H "Content-Type: application/json" \
  -d '{"producto":"Servilletero","cantidad":50}'
```

---

## ⚙️ PRÓXIMAS MEJORAS

**Roadmap (próximas 4 semanas):**

**Semana 1:** Testing automation  
**Semana 2:** 4 nuevos motores  
**Semana 3:** WebSocket real-time + notificaciones  
**Semana 4:** Beta testing en escuela real

---

## ❓ FAQ

**P: ¿Necesito Python instalado?**  
R: Sí, pero pronto empaquetaremos un .exe que no lo requiere.

**P: ¿Funciona offline?**  
R: Sí, completamente. Solo HTTP puro.

**P: ¿Es seguro?**  
R: Sí, todo está en tu PC. Sin datos en nube.

**P: ¿Cómo agrego más motores?**  
R: Copia la estructura de motor_coaching, rellena con tu lógica.

**P: ¿Y si alguien está en crisis real?**  
R: AURORA detecta automáticamente y alerta a adultos sin que lo sepa.

---

## 🚀 ESTADO

| Feature | Status |
|---------|--------|
| Chat coaching | ✅ Operativo |
| Crisis protocol | ✅ Operativo |
| Cotizador | ✅ Operativo |
| Database | ✅ Operativo |
| Panel web | ✅ Operativo |
| 6 roles | ✅ Listos |
| Multi-SDK | ✅ Activo |

---

## 📞 SOPORTE

Si algo no funciona:
1. Verifica que Python esté instalado
2. Abre C:\AURORA\CORE\servidor_aurora.py
3. Lee los logs en console

---

**¡AURORA está VIVO y OPERATIVO!**

Próximo: PyInstaller → Empaquetado como .exe único

