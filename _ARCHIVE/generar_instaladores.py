#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                             ║
║          🔧 GENERADOR DE INSTALADORES PROFESIONALES (.MSI / .EXE) 🔧      ║
║                                                                             ║
║  Crea instaladores profesionales para ATF y MILENS                        ║
║  Usa NSIS para crear instaladores de desinstalación automática            ║
║                                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import os
import subprocess
import sys
from pathlib import Path


def generar_instalador_atf():
    """Genera instalador profesional para ATF"""

    print("\n" + "="*80)
    print("🔧 GENERADOR DE INSTALADOR - ATF RETROFIT")
    print("="*80 + "\n")

    # Script NSIS para ATF
    nsis_atf = '''
; ATF Retrofit - Instalador Profesional
; Generado automáticamente

!include "MUI2.nsh"
!include "x64.nsh"

; Nombre de la aplicación
Name "ATF Retrofit App"
OutFile "ATF_Retrofit_Setup.exe"

; Directorio de instalación por defecto
InstallDir "$PROGRAMFILES64\\ATF_Retrofit"

; Solicitar privilegios de administrador
RequestExecutionLevel admin

; Definir MUI
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Idioma
!insertmacro MUI_LANGUAGE "Spanish"

; Instalación
Section "Instalar ATF Retrofit App"
    SetOutPath "$INSTDIR"

    ; Copiar archivos
    File "dist_atf\\ATF_Retrofit_App.exe"
    File "requirements.txt"
    File /r "CORE"

    ; Crear acceso directo en Escritorio
    CreateDirectory "$SMPROGRAMS\\ATF Retrofit"
    CreateShortcut "$SMPROGRAMS\\ATF Retrofit\\ATF Retrofit App.lnk" "$INSTDIR\\ATF_Retrofit_App.exe"
    CreateShortcut "$DESKTOP\\ATF Retrofit App.lnk" "$INSTDIR\\ATF_Retrofit_App.exe"

    ; Guardar información de desinstalación
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ATF_Retrofit" \\
        "DisplayName" "ATF Retrofit App"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ATF_Retrofit" \\
        "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ATF_Retrofit" \\
        "DisplayIcon" "$INSTDIR\\ATF_Retrofit_App.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ATF_Retrofit" \\
        "DisplayVersion" "1.0.0"

    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

; Desinstalación
Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\ATF Retrofit"
    Delete "$DESKTOP\\ATF Retrofit App.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\ATF_Retrofit"
SectionEnd
'''

    with open("atf_installer.nsi", "w", encoding="utf-8") as f:
        f.write(nsis_atf)

    print("✅ Script NSIS para ATF creado\n")

    return "atf_installer.nsi"


def generar_instalador_milens():
    """Genera instalador profesional para MILENS"""

    print("🔧 GENERADOR DE INSTALADOR - MILENS\n")

    # Script NSIS para MILENS
    nsis_milens = '''
; MILENS - Instalador Profesional
; Generado automáticamente

!include "MUI2.nsh"
!include "x64.nsh"

; Nombre de la aplicación
Name "Milens App"
OutFile "Milens_Setup.exe"

; Directorio de instalación por defecto
InstallDir "$PROGRAMFILES64\\Milens"

; Solicitar privilegios de administrador
RequestExecutionLevel admin

; Definir MUI
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Idioma
!insertmacro MUI_LANGUAGE "Spanish"

; Instalación
Section "Instalar Milens App"
    SetOutPath "$INSTDIR"

    ; Copiar archivos
    File "dist_milens\\Milens_App.exe"
    File "requirements.txt"
    File /r "CORE"

    ; Crear acceso directo en Escritorio
    CreateDirectory "$SMPROGRAMS\\Milens"
    CreateShortcut "$SMPROGRAMS\\Milens\\Milens App.lnk" "$INSTDIR\\Milens_App.exe"
    CreateShortcut "$DESKTOP\\Milens App.lnk" "$INSTDIR\\Milens_App.exe"

    ; Guardar información de desinstalación
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Milens" \\
        "DisplayName" "Milens App"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Milens" \\
        "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Milens" \\
        "DisplayIcon" "$INSTDIR\\Milens_App.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Milens" \\
        "DisplayVersion" "1.0.0"

    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

; Desinstalación
Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\Milens"
    Delete "$DESKTOP\\Milens App.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Milens"
SectionEnd
'''

    with open("milens_installer.nsi", "w", encoding="utf-8") as f:
        f.write(nsis_milens)

    print("✅ Script NSIS para MILENS creado\n")

    return "milens_installer.nsi"


def crear_batch_instalacion():
    """Crea script batch para automatizar todo"""

    batch_content = '''@echo off
REM ════════════════════════════════════════════════════════════════════════════════
REM    🚀 INSTALADOR AUTOMÁTICO - ATF Y MILENS
REM ════════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║                   🚀 INSTALADOR AUTOMÁTICO                               ║
echo ║                                                                            ║
echo ║         Creando aplicaciones ejecutables para ATF y MILENS                 ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Instalar dependencias
echo 📦 Instalando dependencias...
pip install pyinstaller -q
echo ✅ PyInstaller instalado
echo.

REM Crear ATF EXE
echo 🏗️  Creando ejecutable ATF...
python crear_exe_atf.py
if errorlevel 1 (
    echo ❌ Error creando ATF EXE
    pause
    exit /b 1
)
echo ✅ ATF EXE creado exitosamente
echo.

REM Crear MILENS EXE
echo 🏗️  Creando ejecutable MILENS...
python crear_exe_milens.py
if errorlevel 1 (
    echo ❌ Error creando MILENS EXE
    pause
    exit /b 1
)
echo ✅ MILENS EXE creado exitosamente
echo.

REM Mostrar resultado final
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo ✅ APLICACIONES CREADAS EXITOSAMENTE
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 📦 ARCHIVOS GENERADOS:
echo    • dist_atf\\ATF_Retrofit_App.exe (ATF)
echo    • dist_milens\\Milens_App.exe (MILENS)
echo.
echo 🚀 PRÓXIMOS PASOS:
echo    1. Para instalar en tu PC:
echo       - Doble clic en dist_atf\\ATF_Retrofit_App.exe
echo    2. Para instalar en PC de tu esposa:
echo       - Doble clic en dist_milens\\Milens_App.exe
echo    3. Ambas aplicaciones se ejecutarán 24/7 en background
echo.
echo 💾 UBICACIÓN:
echo    • ATF: %PROGRAMFILES%\\ATF_Retrofit\\
echo    • MILENS: %PROGRAMFILES%\\Milens\\
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo.

pause
'''

    with open("INSTALAR_TODO.bat", "w", encoding="utf-8") as f:
        f.write(batch_content)

    print("\n✅ Script de instalación automático creado: INSTALAR_TODO.bat\n")


def mostrar_resumen_final():
    """Muestra resumen final"""

    print("\n" + "="*80)
    print("✅ GENERADORES DE INSTALADORES CREADOS")
    print("="*80)
    print("""
📋 ARCHIVOS GENERADOS:

1. atf_installer.nsi
   └─ Script para instalador ATF

2. milens_installer.nsi
   └─ Script para instalador MILENS

3. INSTALAR_TODO.bat
   └─ Script automático para generar todo

📦 CÓMO GENERAR LOS INSTALADORES:

Opción 1 - Automático (Recomendado):
   1. Doble clic en: INSTALAR_TODO.bat
   2. Esperar a que se complete (~3-5 minutos)
   3. Los ejecutables estarán en:
      • dist_atf/ATF_Retrofit_App.exe
      • dist_milens/Milens_App.exe

Opción 2 - Manual:
   1. python crear_exe_atf.py
   2. python crear_exe_milens.py

✅ INSTALACIÓN FINAL:

ATF (para ti):
   1. Doble clic en: dist_atf/ATF_Retrofit_App.exe
   2. Se abrirá automáticamente en http://localhost:8000

MILENS (para tu esposa):
   1. Doble clic en: dist_milens/Milens_App.exe
   2. Se abrirá automáticamente en http://localhost:8001

🎯 CARACTERÍSTICAS:
   ✅ Publicador multi-red automático
   ✅ Búsqueda de productos en tiempo real
   ✅ ChatBot WhatsApp inteligente
   ✅ Dashboard analytics
   ✅ Completamente autónomo 24/7
   ✅ Sin intervención manual requerida

═════════════════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔧 GENERADOR DE INSTALADORES PROFESIONALES")
    print("="*80 + "\n")

    # Generar scripts
    atf_script = generar_instalador_atf()
    milens_script = generar_instalador_milens()

    # Crear batch automático
    crear_batch_instalacion()

    # Mostrar resumen
    mostrar_resumen_final()

    print("\n🚀 Para comenzar, ejecuta: INSTALAR_TODO.bat\n")
