# -*- coding: utf-8 -*-
"""AURORA · CARTUCHO WEB REAL — navegación/búsqueda en vivo (sin API key).

Usa DuckDuckGo (HTML) para buscar de verdad en internet y extrae texto real de
una página. Cero invento: devuelve lo que la web dice ahora mismo.
"""
from __future__ import annotations
import re, html as _html
from urllib.parse import unquote, urlparse
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def _limpia(t: str) -> str:
    return _html.unescape(re.sub(r"<.*?>", "", t or "")).strip()


def _desredirige(href: str) -> str:
    """DuckDuckGo envuelve URLs en /l/?uddg=... — las desenvuelve."""
    if "duckduckgo.com/l/" in href or href.startswith("//duckduckgo.com/l/"):
        m = re.search(r"[?&]uddg=([^&]+)", href)
        if m:
            return unquote(m.group(1))
    if href.startswith("//"):
        return "https:" + href
    return href


def buscar(consulta: str, n: int = 6, region: str = "mx-es") -> dict:
    """Busca en internet AHORA (DuckDuckGo vía ddgs) y devuelve títulos, URLs y extractos reales."""
    if not consulta or not consulta.strip():
        return {"status": "error", "mensaje": "Consulta vacía"}
    try:
        from ddgs import DDGS
        res = list(DDGS().text(consulta, region=region, max_results=n))
    except Exception as e:
        return {"status": "error", "mensaje": f"Búsqueda falló: {e}"}
    resultados = []
    for x in res:
        url = x.get("href", "") or x.get("url", "")
        resultados.append({"titulo": x.get("title", ""), "url": url,
                           "dominio": urlparse(url).netloc, "extracto": x.get("body", "")})
    return {"status": "ok", "consulta": consulta, "total": len(resultados),
            "resultados": resultados}


def noticias(consulta: str, n: int = 6, region: str = "mx-es") -> dict:
    """Noticias recientes reales sobre un tema."""
    try:
        from ddgs import DDGS
        res = list(DDGS().news(consulta, region=region, max_results=n))
    except Exception as e:
        return {"status": "error", "mensaje": f"Noticias falló: {e}"}
    items = [{"titulo": x.get("title", ""), "url": x.get("url", ""),
              "fuente": x.get("source", ""), "fecha": x.get("date", ""),
              "extracto": x.get("body", "")} for x in res]
    return {"status": "ok", "consulta": consulta, "total": len(items), "noticias": items}


def leer_pagina(url: str, max_chars: int = 4000) -> dict:
    """Abre una URL y extrae su TEXTO real (sin scripts/estilos)."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        r = requests.get(url, headers=UA, timeout=15)
    except Exception as e:
        return {"status": "error", "mensaje": f"No se pudo abrir: {e}"}
    if r.status_code != 200:
        return {"status": "error", "mensaje": f"La página respondió HTTP {r.status_code}", "url": url}
    h = r.text
    h = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav).*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", h)
    texto = _limpia(h)
    texto = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]{2,}", " ", texto))
    titulo = ""
    mt = re.search(r"(?is)<title>(.*?)</title>", r.text)
    if mt:
        titulo = _limpia(mt.group(1))
    return {"status": "ok", "url": url, "titulo": titulo,
            "texto": texto[:max_chars], "chars": len(texto)}


def contexto_para_llm(consulta: str, n: int = 4) -> str:
    """Empaqueta resultados reales de la web como contexto para el cerebro."""
    r = buscar(consulta, n)
    if r.get("status") != "ok" or not r["resultados"]:
        return ""
    partes = [f"Resultados web reales para '{consulta}':"]
    for i, x in enumerate(r["resultados"], 1):
        partes.append(f"{i}. {x['titulo']} ({x['dominio']}) — {x['extracto'][:200]}")
    return "\n".join(partes)


if __name__ == "__main__":
    import sys, json
    q = " ".join(sys.argv[1:]) or "precio laser co2 100w mexico"
    print(json.dumps(buscar(q), ensure_ascii=False, indent=2))
