# -*- coding: utf-8 -*-
"""Cuenta los duplicados REALES de AURORA, leyendo el código, no adivinando.

Anuar lo preguntó así: *"me brinca que siempre salen cosas en 2 lados, cuántos
duplicados hay en todo el sistema"*. Tiene razón en que le brinque: los precios
estaban en dos lados, la regla del DXF estaba en dos lados, las frases estaban
en dos lados. Esto pone el número.

Separa dos cosas que NO son lo mismo:
  * COPIA EXACTA  — mismo nombre y mismo código en dos archivos. Es puro peso
    muerto: se arregla uno y el otro se queda viejo sin que nadie se entere.
  * MISMO NOMBRE, CÓDIGO DISTINTO — el peligroso de verdad. Se ven iguales al
    leerlos, hacen cosas distintas, y nadie sabe cuál corre.
"""
import ast
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(r"C:\AURORA.worktrees")
SALTAR = {"FORJA", "_OBSOLETOS", "EMPAQUETADO", ".git", "node_modules",
          "__pycache__", "BACKUPS", "_FIX_PROPUESTO_20260824", ".claude",
          ".venv", "venv", "site-packages",
          # Librerias de TERCEROS empaquetadas y codigo de referencia rescatado.
          # El primer conteo las metio y dio 192 duplicados "peligrosos" cuando
          # la mayoria eran cffi y cryptography, que no son de Anuar.
          "SUPER_MARKETING_SYSTEM", "_RESCATE_NEXUS", "TEMPLATES"}

# Nombres que se repiten POR CONVENCION, no por descuido: cada script tiene su
# main(), cada modulo su generar()/calcular(). Contarlos como duplicados manda
# a Anuar a perseguir fantasmas. Se reportan aparte, no se esconden.
CONVENCION = {"main", "__main__", "run", "setup", "generar", "calcular",
              "texto", "principal", "ejecutar", "procesar", "iniciar"}

archivos = [p for p in RAIZ.rglob("*.py")
            if not any(s in p.parts for s in SALTAR)]

por_nombre = defaultdict(list)
for p in archivos:
    try:
        arbol = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                cuerpo = ast.dump(ast.Module(body=n.body, type_ignores=[]))
            except Exception:
                cuerpo = ""
            huella = hashlib.md5(cuerpo.encode()).hexdigest()
            rel = str(p.relative_to(RAIZ)).replace("\\", "/")
            por_nombre[n.name].append((rel, huella, len(n.body)))

total_funcs = sum(len(v) for v in por_nombre.values())

identicas, distintas = [], []
for nom, lista in por_nombre.items():
    if nom in CONVENCION or nom.startswith("__") or len(lista) < 2:
        continue
    archs = sorted({a for a, _, _ in lista})
    if len(archs) < 2:
        continue
    huellas = {h for _, h, _ in lista}
    grande = max(t for _, _, t in lista)
    if len(huellas) == 1:
        if grande >= 3:                      # menos de 3 líneas es un stub
            identicas.append((nom, archs, grande))
    elif grande >= 8:                        # cuerpos con sustancia de verdad
        distintas.append((nom, archs, grande))

L = []
L.append("=" * 70)
L.append("  DUPLICADOS REALES DE AURORA")
L.append("=" * 70)
L.append(f"  archivos .py revisados : {len(archivos)}")
L.append(f"  funciones totales      : {total_funcs}")
L.append("")
L.append(f"  COPIAS EXACTAS (mismo nombre Y mismo código): {len(identicas)}")
L.append(f"  MISMO NOMBRE, CÓDIGO DISTINTO (los peligrosos): {len(distintas)}")
peso = sum(t * (len(a) - 1) for _, a, t in identicas)
L.append(f"  líneas de puro peso muerto por las copias: ~{peso}")
L.append("")
L.append("-" * 70)
L.append("  COPIAS EXACTAS — las 15 más grandes")
L.append("-" * 70)
for nom, archs, t in sorted(identicas, key=lambda x: -x[2])[:15]:
    L.append(f"  {nom}  ({t} líneas, en {len(archs)} archivos)")
    for a in archs[:4]:
        L.append(f"      {a}")
L.append("")
L.append("-" * 70)
L.append("  MISMO NOMBRE, CÓDIGO DISTINTO — las 15 más grandes")
L.append("  (éstos son los que se desincronizan sin avisar)")
L.append("-" * 70)
for nom, archs, t in sorted(distintas, key=lambda x: -x[2])[:15]:
    L.append(f"  {nom}  ({t} líneas, en {len(archs)} archivos)")
    for a in archs[:4]:
        L.append(f"      {a}")

salida = RAIZ / "_CONTEXTO" / "DUPLICADOS.txt"
salida.write_text("\r\n".join(L), encoding="utf-8-sig", newline="")
print("\n".join(L[:12]))
print(f"\n-> {salida}")
