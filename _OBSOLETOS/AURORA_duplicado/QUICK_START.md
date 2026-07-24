# ⚡ QUICK START - AURORA v3 EN 5 MINUTOS

## Paso 1️⃣ : Instalar Dependencias
```powershell
cd C:\AURORA
.\\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
**Tiempo: 2-3 minutos** ⏱️

---

## Paso 2️⃣ : Verificar Configuración
```powershell
python validar_aurora.py
```

Debe mostrar:
```
✅ Estructura: PASS
✅ Configuración: PASS
✅ Dependencias: PASS
✅ Base de Datos: PASS
✅ APIs: PASS
```
**Tiempo: 30 segundos** ⏱️

---

## Paso 3️⃣ : Generar Token JWT (opcional, para testing)
```powershell
python generar_token_jwt.py
```

Respuesta:
```
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
**Tiempo: 10 segundos** ⏱️

---

## Paso 4️⃣ : Arrancar Aurora
```powershell
python run_aurora.py
```

Verás:
```
╔════════════════════════════════════════════════════════════╗
║  ✅ AURORA COMPLETAMENTE OPERATIVO                         ║
║  🌐 Accede a: http://localhost:5000                       ║
║  📚 Docs: http://localhost:5000/api/docs                  ║
║  💬 WhatsApp: ESCUCHANDO                                  ║
║  📤 Publicador: LISTO                                     ║
╚════════════════════════════════════════════════════════════╝
```
**Tiempo: 10 segundos** ⏱️

---

## 🌐 Acceder a la API

### En navegador
- Dashboard: http://localhost:5000
- Docs: http://localhost:5000/api/docs
- Health: http://localhost:5000/api/health

### Con curl (Login)
```bash
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"usuario_id": "admin", "password": "admin"}'
```

### Copiar token y usar
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Obtener estado
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/status
```

---

## ✅ FUNCIONALIDADES ACTIVAS

| Feature | Status | Endpoint |
|---------|--------|----------|
| WhatsApp Listener | ✅ Activo | (background) |
| Facebook Publisher | ✅ Activo | POST /api/publicador/crear |
| Instagram Publisher | ✅ Activo | POST /api/publicador/crear |
| CRM Sistema | ✅ Activo | (backend) |
| Dashboard | ✅ Activo | GET / |
| JWT Auth | ✅ Activo | POST /api/auth/login |
| API Health | ✅ Activo | GET /api/health |

---

## 🐛 SI ALGO FALLA

### Error: "Token inválido"
```bash
# Solución: Generar nuevo token
python generar_token_jwt.py
```

### Error: "Puerto 5000 en uso"
```powershell
# Buscar qué proceso usa el puerto
netstat -ano | findstr :5000

# Liberar puerto
taskkill /PID <PID> /F
```

### Error: ".env no encontrado"
```bash
# Copiar template
cp .env.example .env
# Editar con tus credenciales reales
notepad .env
```

### Logs de error
```powershell
Get-Content C:\AURORA\LOGS\aurora.log -Tail 50
```

---

## 📚 DOCUMENTACIÓN COMPLETA

Ver `README.md` para documentación completa, ejemplos de código, troubleshooting avanzado, etc.

---

## 🎯 PRÓXIMOS PASOS

1. ✅ **Ahora**: Aurora está corriendo en localhost:5000
2. 📝 **Siguiente**: Crear leads en CRM
3. 🚀 **Luego**: Publicar en redes sociales
4. 📊 **Final**: Ver analytics en dashboard

---

**¡Aurora está listo! 🚀**

Cualquier pregunta: Ver README.md o revisar logs en C:\AURORA\LOGS\
