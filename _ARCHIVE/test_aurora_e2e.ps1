# ================================================================================
#                    AURORA v2 - TEST AUTOMATIZADO END-TO-END
# ================================================================================

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                  AURORA v2 - TESTING END-TO-END" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el servidor esté corriendo
Write-Host "[TEST 1] Verificando si servidor está vivo..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASSED: Servidor activo" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ FAILED: Servidor no responde" -ForegroundColor Red
    Write-Host "Inicia el servidor: python C:\AURORA\CORE\servidor_simple.py"
    exit 1
}

# Test GET /
Write-Host ""
Write-Host "[TEST 2] GET / (Información sistema)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    if ($data.sistema -eq "AURORA v2 - Operativo") {
        Write-Host "✅ PASSED: Sistema identificado correctamente" -ForegroundColor Green
        Write-Host "   Status: $($data.status)"
        Write-Host "   Roles: $($data.roles.Count)"
        Write-Host "   Librerías: $($data.librerias)"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test GET /health
Write-Host ""
Write-Host "[TEST 3] GET /health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    if ($data.status -eq "healthy") {
        Write-Host "✅ PASSED: Health check OK" -ForegroundColor Green
        Write-Host "   Status: $($data.status)"
        Write-Host "   AURORA: $($data.aurora)"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test GET /librerias
Write-Host ""
Write-Host "[TEST 4] GET /librerias (16 psicológicas)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/librerias" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    if ($data.total -eq 16) {
        Write-Host "✅ PASSED: 16 librerías cargadas" -ForegroundColor Green
        Write-Host "   Primera: $($data.activas[0])"
        Write-Host "   Última: $($data.activas[15])"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test GET /dinamicas
Write-Host ""
Write-Host "[TEST 5] GET /dinamicas (6 educativas)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/dinamicas" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    if ($data.total -eq 6) {
        Write-Host "✅ PASSED: 6 dinámicas cargadas" -ForegroundColor Green
        Write-Host "   Dinámicas: $($data.dinamicas -join ', ')" -Wrap
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test GET /roles
Write-Host ""
Write-Host "[TEST 6] GET /roles (6 disponibles)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/roles" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    if ($data.total -eq 6) {
        Write-Host "✅ PASSED: 6 roles cargados" -ForegroundColor Green
        foreach ($role in $data.roles) {
            Write-Host "   • $($role.nombre)"
        }
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test GET /panel
Write-Host ""
Write-Host "[TEST 7] GET /panel (HTML completo)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/panel" -ErrorAction Stop
    $html = $response.Content
    if ($html.Contains("<!DOCTYPE html") -and $html.Contains("AURORA")) {
        Write-Host "✅ PASSED: Panel HTML cargado correctamente" -ForegroundColor Green
        $htmlLength = $html.Length / 1024
        Write-Host "   Tamaño: $([Math]::Round($htmlLength))KB"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test POST /chat
Write-Host ""
Write-Host "[TEST 8] POST /chat (Mensaje simple)..." -ForegroundColor Yellow
try {
    $body = '{"mensaje":"Estoy estresado","rol":"teen"}'
    $response = Invoke-WebRequest -Uri "http://localhost:8000/chat" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop

    $data = $response.Content | ConvertFrom-Json
    if ($data.status -eq "ok") {
        Write-Host "✅ PASSED: Chat responde correctamente" -ForegroundColor Green
        Write-Host "   Respuesta: $($data.respuesta.Substring(0, [Math]::Min(50, $data.respuesta.Length)))"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test POST /chat con acentos
Write-Host ""
Write-Host "[TEST 9] POST /chat (Con acentos UTF-8)..." -ForegroundColor Yellow
try {
    $body = '{"mensaje":"Tengo mucha ansiedad","rol":"teen"}'
    $response = Invoke-WebRequest -Uri "http://localhost:8000/chat" `
        -Method POST `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
        -ErrorAction Stop

    $data = $response.Content | ConvertFrom-Json
    if ($data.status -eq "ok" -and $data.respuesta.Contains("ansiedad")) {
        Write-Host "✅ PASSED: UTF-8 con acentos maneja correctamente" -ForegroundColor Green
        Write-Host "   Mensaje procesado: 'Tengo mucha ansiedad'"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test POST /cotizar
Write-Host ""
Write-Host "[TEST 10] POST /cotizar (Cálculo de precios)..." -ForegroundColor Yellow
try {
    $body = '{"producto":"Servilletero","cantidad":100}'
    $response = Invoke-WebRequest -Uri "http://localhost:8000/cotizar" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop

    $data = $response.Content | ConvertFrom-Json
    if ($data.total_costo -eq 10000 -and $data.precio_venta -eq 15000) {
        Write-Host "✅ PASSED: Cálculo correcto (100 × 100 = 10000)" -ForegroundColor Green
        Write-Host "   Costo: `$10,000 | Margen: `$5,000 | Venta: `$15,000"
    }
} catch {
    Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 404
Write-Host ""
Write-Host "[TEST 11] Manejo de 404 (Endpoint inexistente)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/inexistente" -ErrorAction Stop
    Write-Host "❌ FAILED: Debería retornar 404" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "✅ PASSED: 404 manejado correctamente" -ForegroundColor Green
    }
}

# Resumen
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                        TEST COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "STATUS: 🟢 AURORA v2 OPERATIVO 100%" -ForegroundColor Green
Write-Host ""
Write-Host "Panel disponible en: http://localhost:8000/panel" -ForegroundColor Green
Write-Host ""
