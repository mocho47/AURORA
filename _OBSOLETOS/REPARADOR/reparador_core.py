# -*- coding: utf-8 -*-
"""Reparador de apps de Windows (UWP/Tienda) para AURORA.
Arregla apps colgadas (WhatsApp, Spotify, etc.): mata procesos zombie, re-registra el paquete
(no destructivo) y, si se pide, resetea (borra datos)."""
import subprocess

def _ps(script: str) -> str:
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                           capture_output=True, text=True, timeout=120)
        return ((r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")).strip()
    except Exception as e:
        return f"ERR:{e}"

def listar(filtro: str = "") -> dict:
    out = _ps(f"Get-AppxPackage *{filtro}* | Select-Object -ExpandProperty Name")
    apps = [l.strip() for l in out.splitlines() if l.strip()]
    return {"status": "OK", "apps": apps[:80]}

def reparar(nombre: str, reset: bool = False, abrir: bool = False) -> dict:
    if not nombre:
        return {"status": "ERROR", "detalle": "Falta el nombre de la app"}
    res = {"status": "OK", "app": nombre, "pasos": []}
    # 1. matar procesos zombie
    _ps(f"Get-Process | Where-Object {{ $_.ProcessName -like '*{nombre}*' }} | Stop-Process -Force -ErrorAction SilentlyContinue")
    res["pasos"].append("procesos detenidos")
    # 2. verificar que exista el paquete
    pkg = _ps(f"(Get-AppxPackage *{nombre}*).PackageFullName")
    if not pkg or "ERR:" in pkg:
        return {"status": "ERROR", "app": nombre, "detalle": "No encontré ese paquete instalado"}
    res["paquete"] = pkg.splitlines()[0][:120]
    if reset:
        # 3a. RESET (borra datos: re-login/re-vincular)
        rs = _ps(f"Get-AppxPackage *{nombre}* | Reset-AppxPackage")
        res["pasos"].append("RESET (datos borrados)")
        res["detalle_reset"] = rs[:200]
    else:
        # 3b. re-registrar (NO destructivo)
        _ps("Get-AppxPackage *" + nombre + "* | ForEach-Object { Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppXManifest.xml\" -ErrorAction SilentlyContinue }")
        res["pasos"].append("re-registrado (sin perder datos)")
    if abrir:
        _ps(f"$id=(Get-AppxPackage *{nombre}*).PackageFamilyName; if($id){{ Start-Process \"shell:AppsFolder\\$id!App\" -ErrorAction SilentlyContinue }}")
        res["pasos"].append("intento de apertura")
    return res
