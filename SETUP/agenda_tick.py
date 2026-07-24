# -*- coding: utf-8 -*-
"""Tick del agendador: pide a AURORA publicar lo APROBADO cuya hora llegó.
Lo ejecuta la tarea programada (no publica nada que Anuar no haya aprobado)."""
import urllib.request, sys
try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/agenda/publicar-pendientes", method="POST")
    print(urllib.request.urlopen(req, timeout=600).read().decode()[:300])
except Exception as e:
    print("tick error:", e); sys.exit(1)
