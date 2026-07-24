# -*- coding: utf-8 -*-
"""
AURORA · BIBLIOTECA DE CONOCIMIENTO
Ingiere manuales/PDF y los deja BUSCABLES (SQLite FTS5, sin depender de nube).
AURORA los consulta para "fluir en el entorno" de Anuar (RDWorks, Corel, Aspire, etc.).
Real: extracción con PyMuPDF, búsqueda full-text nativa. Cero simulación.

BÚSQUEDA SEMÁNTICA (aditiva, con fallback):
Además de FTS5, guarda embeddings (Ollama nomic-embed-text, 100% local) y busca
por SIGNIFICADO. Si Ollama no está o no hay vectores, cae SOLO a FTS5 (idéntico a antes).
Las firmas públicas NO cambian: ingerir_pdf, buscar, contexto_para_llm, estado.
"""
from __future__ import annotations
import re
import json
import math
import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

try:
    from urllib import request as _urlreq
except Exception:  # pragma: no cover
    _urlreq = None

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "biblioteca.db"

OLLAMA_URL = "http://127.0.0.1:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def _con():
    con = sqlite3.connect(str(DB))
    return con


def init_db() -> None:
    con = _con()
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(documento, pagina, texto)")
    # Tabla de embeddings semánticos (misma DB). vector = json.dumps(list[float]).
    con.execute("CREATE TABLE IF NOT EXISTS emb (documento TEXT, pagina TEXT, vector TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_emb_doc_pag ON emb (documento, pagina)")
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# EMBEDDINGS (Ollama, local). Todo best-effort: NUNCA lanza.
# ---------------------------------------------------------------------------
def _embed(texto: str):
    """POST a Ollama /api/embeddings. Devuelve list[float] o None si algo falla."""
    if not texto or _urlreq is None:
        return None
    try:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": texto}).encode("utf-8")
        req = _urlreq.Request(OLLAMA_URL, data=payload,
                              headers={"Content-Type": "application/json"})
        with _urlreq.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        vec = data.get("embedding")
        if isinstance(vec, list) and vec:
            return [float(x) for x in vec]
    except Exception:
        return None
    return None


def _cos(a, b) -> float:
    """Coseno entre dos listas. 0.0 si algo no cuadra."""
    try:
        n = min(len(a), len(b))
        if n == 0:
            return 0.0
        dot = 0.0
        na = 0.0
        nb = 0.0
        for i in range(n):
            x = a[i]
            y = b[i]
            dot += x * y
            na += x * x
            nb += y * y
        if na <= 0 or nb <= 0:
            return 0.0
        return dot / (math.sqrt(na) * math.sqrt(nb))
    except Exception:
        return 0.0


def _emb_existentes(con) -> set:
    """Set de (documento, pagina) que ya tienen embedding."""
    try:
        return {(r[0], r[1]) for r in con.execute("SELECT documento, pagina FROM emb").fetchall()}
    except Exception:
        return set()


def reindexar_semantica(limite_paginas: int = 60) -> dict:
    """
    Calcula embeddings para páginas de 'docs' que aún no lo tengan.
    LÍMITE por corrida (default 60) para no saturar RAM (8GB). Se puede correr varias veces.
    Devuelve cuántas indexó y cuántas faltan.
    """
    init_db()
    con = _con()
    try:
        filas = con.execute("SELECT documento, pagina, texto FROM docs").fetchall()
    except Exception:
        con.close()
        return {"status": "error", "indexadas": 0, "faltan": 0, "mensaje": "sin tabla docs"}

    ya = _emb_existentes(con)
    pendientes = [f for f in filas if (f[0], f[1]) not in ya]

    indexadas = 0
    fallos = 0
    for doc, pag, txt in pendientes[:max(0, limite_paginas)]:
        vec = _embed((txt or "")[:2000])
        if vec is None:
            fallos += 1
            # Si Ollama no responde, no tiene sentido seguir martillando.
            if fallos >= 3 and indexadas == 0:
                break
            continue
        try:
            con.execute("INSERT INTO emb (documento, pagina, vector) VALUES (?,?,?)",
                        (doc, pag, json.dumps(vec)))
            indexadas += 1
        except Exception:
            pass
    con.commit()
    con.close()
    faltan = max(0, len(pendientes) - indexadas)
    return {"status": "ok", "indexadas": indexadas, "faltan": faltan,
            "total_paginas": len(filas)}


def _buscar_semantica(consulta: str, limite: int, con) -> list:
    """
    Devuelve [(documento, pagina, score)] por similitud coseno.
    Lista vacía si no hay vectores o Ollama no responde. Nunca lanza.
    """
    try:
        filas = con.execute("SELECT documento, pagina, vector FROM emb").fetchall()
    except Exception:
        return []
    if not filas:
        return []
    qv = _embed(consulta)
    if qv is None:
        return []
    puntuados = []
    for doc, pag, vjson in filas:
        try:
            vec = json.loads(vjson)
        except Exception:
            continue
        puntuados.append((doc, pag, _cos(qv, vec)))
    puntuados.sort(key=lambda t: t[2], reverse=True)
    # Filtra ruido: coseno muy bajo no aporta.
    puntuados = [p for p in puntuados if p[2] > 0.3]
    return puntuados[:max(1, limite) * 2]


def ingerir_pdf(ruta: str, nombre: str = "") -> dict:
    init_db()
    p = Path(ruta)
    if not p.exists():
        return {"status": "error", "mensaje": f"No existe: {ruta}"}
    nombre = nombre or p.stem
    try:
        d = fitz.open(ruta)
    except Exception as e:
        return {"status": "error", "mensaje": f"No se pudo abrir: {e}"}
    con = _con()
    con.execute("DELETE FROM docs WHERE documento=?", (nombre,))
    # Limpia embeddings viejos del mismo doc (se recalculan abajo).
    try:
        con.execute("DELETE FROM emb WHERE documento=?", (nombre,))
    except Exception:
        pass
    n = 0
    paginas_nuevas = []  # (pagina, texto)
    for i, page in enumerate(d):
        txt = page.get_text().strip()
        if txt:
            pag = str(i + 1)
            con.execute("INSERT INTO docs (documento, pagina, texto) VALUES (?,?,?)",
                        (nombre, pag, txt))
            paginas_nuevas.append((pag, txt))
            n += 1
    con.commit()

    # Best-effort: indexar semánticamente las páginas nuevas. Si falla, ni modo.
    emb_ok = 0
    try:
        for pag, txt in paginas_nuevas:
            vec = _embed(txt[:2000])
            if vec is None:
                break  # Ollama no disponible: abortar sin romper la ingesta.
            con.execute("INSERT INTO emb (documento, pagina, vector) VALUES (?,?,?)",
                        (nombre, pag, json.dumps(vec)))
            emb_ok += 1
        con.commit()
    except Exception:
        pass

    con.close()
    return {"status": "ok", "documento": nombre, "paginas_con_texto": n,
            "paginas_total": len(d), "paginas_embebidas": emb_ok}


# Glosario ES→EN: los manuales (RDWorks/Ruida/K10) están en inglés y Anuar pregunta
# en español. Expandir la consulta con los equivalentes hace que el RAG SÍ encuentre.
_GLOSARIO = {
    "velocidad": ["speed"], "potencia": ["power"], "corte": ["cut", "cutting"],
    "cortar": ["cut"], "grabado": ["engrave", "engraving", "scan"], "grabar": ["engrave"],
    "capa": ["layer"], "capas": ["layers"], "archivo": ["file"], "importar": ["import"],
    "exportar": ["export"], "configuracion": ["settings", "config"], "ajuste": ["setting"],
    "ajustes": ["settings"], "enfoque": ["focus"], "maquina": ["machine"],
    "trabajo": ["job", "work"], "origen": ["origin"], "posicion": ["position"],
    "relleno": ["fill", "scan"], "linea": ["line"], "frecuencia": ["frequency"],
    "espesor": ["thickness"], "prueba": ["test"], "borde": ["edge"], "esquina": ["corner"],
    "controlador": ["controller"], "panel": ["panel"], "boton": ["key", "button"],
    "eje": ["axis"], "pausa": ["pause"], "inicio": ["start", "origin"], "marco": ["frame"],
}
_STOP = {"de", "la", "el", "los", "las", "un", "una", "que", "como", "con", "por", "para",
         "del", "mas", "muy", "sus", "este", "esta", "segun", "tengo", "puedo", "hay",
         "the", "and", "for", "with", "how", "can"}


def _fts_query(consulta: str) -> str:
    # tokens seguros para FTS5, con expansión ES→EN, OR entre palabras
    tokens = re.findall(r"\w+", consulta.lower(), flags=re.UNICODE)
    exp = set()
    for t in tokens:
        if len(t) <= 2 or t in _STOP:
            continue
        exp.add(t)
        for en in _GLOSARIO.get(t, []):
            exp.add(en)
    if not exp:
        return '""'
    return " OR ".join(exp)


def buscar(consulta: str, limite: int = 4) -> dict:
    """
    HÍBRIDO: combina FTS5 (palabras) + similitud semántica (significado, vía embeddings).
    Prioriza las páginas que aparecen en AMBOS. Si no hay Ollama/vectores, cae a SOLO FTS5.
    Formato de salida IDÉNTICO al original.
    """
    init_db()
    con = _con()

    # --- FTS5 (comportamiento original) ---
    q = _fts_query(consulta)
    fts_rows = []
    try:
        fts_rows = con.execute(
            "SELECT documento, pagina, texto FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
            (q, max(limite, 8)),
        ).fetchall()
    except Exception:
        fts_rows = []

    # --- Semántica (best-effort) ---
    sem = []
    try:
        sem = _buscar_semantica(consulta, limite, con)
    except Exception:
        sem = []

    # Si no hubo nada semántico, replicar EXACTAMENTE el comportamiento anterior.
    if not sem:
        con.close()
        rows = fts_rows[:limite]
        return {"status": "ok", "consulta": consulta,
                "resultados": [{"documento": r[0], "pagina": r[1], "fragmento": r[2][:600]}
                               for r in rows]}

    # --- Fusión ---
    # Ranking FTS: mejor posición = mayor score (rank ya viene ordenado).
    fts_pos = {}
    for idx, r in enumerate(fts_rows):
        fts_pos[(r[0], r[1])] = idx
    fts_score = {}
    nfts = len(fts_rows)
    for (doc, pag), idx in fts_pos.items():
        fts_score[(doc, pag)] = (nfts - idx) / nfts if nfts else 0.0

    sem_score = {(doc, pag): score for doc, pag, score in sem}

    claves = set(fts_score) | set(sem_score)
    combinado = []
    for k in claves:
        f = fts_score.get(k, 0.0)
        s = sem_score.get(k, 0.0)
        en_ambos = k in fts_score and k in sem_score
        # Semántica pesa un poco más (significado); bonus fuerte si aparece en ambos.
        total = (0.45 * f) + (0.55 * s) + (0.5 if en_ambos else 0.0)
        combinado.append((k, total))
    combinado.sort(key=lambda t: t[1], reverse=True)

    # Recuperar el texto de cada página elegida.
    texto_cache = {(r[0], r[1]): r[2] for r in fts_rows}
    resultados = []
    for (doc, pag), _score in combinado[:limite]:
        txt = texto_cache.get((doc, pag))
        if txt is None:
            try:
                row = con.execute(
                    "SELECT texto FROM docs WHERE documento=? AND pagina=? LIMIT 1",
                    (doc, pag),
                ).fetchone()
                txt = row[0] if row else ""
            except Exception:
                txt = ""
        resultados.append({"documento": doc, "pagina": pag, "fragmento": (txt or "")[:600]})

    con.close()
    return {"status": "ok", "consulta": consulta, "resultados": resultados}


def contexto_para_llm(consulta: str, limite: int = 3) -> str:
    """Devuelve un bloque de texto de los manuales, para inyectar al cerebro."""
    r = buscar(consulta, limite)
    if not r["resultados"]:
        return ""
    partes = [f"[{x['documento']} p.{x['pagina']}] {x['fragmento']}" for x in r["resultados"]]
    return "CONOCIMIENTO DE MANUALES (consulta interna):\n" + "\n---\n".join(partes)


def estado() -> dict:
    init_db()
    con = _con()
    try:
        docs = con.execute("SELECT documento, COUNT(*) FROM docs GROUP BY documento").fetchall()
    except Exception:
        docs = []
    # Nueva llave: cuántas páginas tienen embedding semántico.
    paginas_embebidas = 0
    try:
        paginas_embebidas = con.execute("SELECT COUNT(*) FROM emb").fetchone()[0]
    except Exception:
        paginas_embebidas = 0
    con.close()
    return {"status": "ok",
            "documentos": [{"nombre": d[0], "paginas": d[1]} for d in docs],
            "paginas_con_embedding": paginas_embebidas}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "estado"
    if cmd == "ingerir":
        print(json.dumps(ingerir_pdf(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""), ensure_ascii=False, indent=2))
    elif cmd == "buscar":
        print(json.dumps(buscar(" ".join(sys.argv[2:])), ensure_ascii=False, indent=2))
    elif cmd == "reindexar":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        print(json.dumps(reindexar_semantica(lim), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(estado(), ensure_ascii=False, indent=2))
