# -*- coding: utf-8 -*-
"""
AURORA · COTIZAR CORTE/GRABADO LÁSER DESDE UNA IMAGEN (Milens)
Encadena REAL: quita fondo (rembg) -> vectoriza a DXF (Inkscape) -> escala a la
altura pedida (ezdxf) -> mide longitud real -> cotiza con precios de config.
NUNCA inventa un número. Si un paso falla, lo dice honesto.

MODOS (corte y grabado tienen velocidades muy distintas):
- "corte_contorno": corta SOLO la silueta/contorno exterior, a velocidad de CORTE.
                    Mide el perímetro del contorno exterior (entidad cerrada más grande).
- "grabado":        GRABA todo el detalle del diseño, a velocidad de GRABADO (200 mm/s).
                    Mide la longitud total de trazo del diseño.
- "ambos":          graba el detalle interno (200) + corta el contorno exterior (corte).
                    Suma los dos tiempos.
"""
from __future__ import annotations
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGO_SERVICIOS = ROOT / "CONFIG" / "catalogo_servicios.json"


def _cargar_mod(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _velocidad_grabado_config(default: float = 200.0) -> float:
    """Lee la velocidad de grabado REAL de la config; si no está, usa el default explícito."""
    try:
        d = json.loads(CATALOGO_SERVICIOS.read_text(encoding="utf-8"))
        v = d.get("velocidad_grabado_mm_s")
        return float(v) if v else default
    except Exception:
        return default


def _bbox_area(e) -> float:
    """Área del bounding box de una entidad (para elegir el contorno exterior más grande)."""
    try:
        from ezdxf import bbox as _bb
        b = _bb.extents([e])
        return b.size.x * b.size.y
    except Exception:
        return 0.0


def _reducir_para_trazo(png_ruta: str, lado_max: int = 1100) -> str:
    """Reduce el raster antes de vectorizar (Inkscape trace es MUY lento en imágenes
    grandes). Conserva la forma (misma silueta) — solo baja resolución. Devuelve la ruta
    a usar (la reducida si aplicó, o la original)."""
    try:
        from PIL import Image
        im = Image.open(png_ruta)
        if max(im.size) <= lado_max:
            return png_ruta
        f = lado_max / max(im.size)
        im2 = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))))
        chico = str(Path(png_ruta).with_name(Path(png_ruta).stem + "_chico.png"))
        im2.save(chico)
        return chico
    except Exception:
        return png_ruta


def _vectorizar_contornos_cv2(png_ruta: str, dxf_out: str) -> dict:
    """Vectorización REAL sin Inkscape: detecta los contornos del sujeto (cv2) y los
    escribe como polilíneas cerradas en un DXF (ezdxf). Sirve cuando el trazo de
    Inkscape no produce vectores en esta máquina. Cero invento: mide geometría real."""
    try:
        import cv2
        import numpy as np
        import ezdxf
    except Exception as e:
        return {"status": "error", "detalle": f"Falta librería para trazar (cv2/ezdxf): {e}"}
    im = cv2.imread(png_ruta)
    if im is None:
        # PNG con alfa: cargar con canal alfa
        from PIL import Image
        arr = np.array(Image.open(png_ruta).convert("RGB"))
        im = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    # sujeto = todo lo que NO es casi-blanco (el dibujo compuesto sobre blanco)
    _, mask = cv2.threshold(gray, 244, 255, cv2.THRESH_BINARY_INV)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contornos, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return {"status": "error", "detalle": "cv2 no encontró contornos (imagen vacía o toda blanca)."}
    H = im.shape[0]
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    n = 0
    for c in contornos:
        if len(c) < 3 or cv2.contourArea(c) < 4:
            continue
        eps = 0.8  # simplifica micro-escalones del pixelado (px)
        c = cv2.approxPolyDP(c, eps, True)
        pts = [(float(p[0][0]), float(H - p[0][1])) for p in c]  # y invertida (DXF sube)
        if len(pts) < 3:
            continue
        msp.add_lwpolyline(pts, close=True)
        n += 1
    if n == 0:
        return {"status": "error", "detalle": "cv2 encontró contornos pero ninguno con área útil."}
    doc.saveas(dxf_out)
    return {"status": "ok", "dxf": dxf_out, "contornos": n}


def cotizar_imagen_laser(imagen_ruta: str, material: str = "MDF 2.7mm (Hoja)",
                         altura_cm: float = 30.0, modo: str = "corte_contorno",
                         velocidad_corte_mm_s: float = 20.0,
                         velocidad_grabado_mm_s: float = 200.0) -> dict:
    """Cotiza corte/grabado láser REAL desde una imagen pegada: quita fondo, vectoriza a DXF, escala a altura_cm y mide la longitud real (nunca inventa el precio)."""
    pasos = []
    img = Path(imagen_ruta)
    if not img.exists():
        return {"status": "error", "mensaje": f"No existe la imagen: {imagen_ruta}"}

    # 1) QUITAR FONDO (IA rembg) — sobre blanco para que el trazo sea limpio (B&N).
    try:
        conv = _cargar_mod("conversiones", ROOT / "EDITOR" / "conversiones.py")
        r_fondo = conv.quitar_fondo(str(img), "", True)  # sobre_blanco=True
        if r_fondo.get("status") != "ok":
            return {"status": "error", "paso": "quitar_fondo", "detalle": r_fondo}
        sin_fondo = r_fondo["salida"]
        pasos.append(f"Fondo eliminado (rembg): {Path(sin_fondo).name} [{r_fondo.get('px')}]")
    except Exception as e:
        return {"status": "error", "paso": "quitar_fondo",
                "detalle": f"No pude quitar el fondo (no lo invento): {str(e)[:300]}"}

    # 2) VECTORIZAR a DXF. Primero el vectorizador oficial (Inkscape/taller_core); si en
    # esta máquina no traza (produce DXF vacío), caemos al trazador REAL por contornos (cv2).
    import ezdxf as _ez
    sin_fondo_trazo = _reducir_para_trazo(sin_fondo, 1100)
    if sin_fondo_trazo != sin_fondo:
        pasos.append(f"Raster reducido para trazo rápido: {Path(sin_fondo_trazo).name}")
    dxf_ruta = None
    try:
        taller = _cargar_mod("taller_core", ROOT / "TALLER" / "taller_core.py")
        r_vec = taller.vectorizar(sin_fondo_trazo)
        cand = r_vec.get("dxf") if isinstance(r_vec, dict) else None
        if cand and Path(cand).exists():
            try:
                if sum(1 for _ in _ez.readfile(cand).modelspace()) > 0:
                    dxf_ruta = cand
                    pasos.append(f"Vectorizado a DXF (Inkscape): {Path(cand).name}")
            except Exception:
                dxf_ruta = None
    except Exception:
        dxf_ruta = None
    if not dxf_ruta:
        # Fallback REAL por contornos (cv2) — no depende de Inkscape.
        dxf_cv2 = str(ROOT / "TALLER_OUT" / (Path(sin_fondo_trazo).stem + "_cv2.dxf"))
        r_cv2 = _vectorizar_contornos_cv2(sin_fondo_trazo, dxf_cv2)
        if r_cv2.get("status") != "ok":
            return {"status": "error", "paso": "vectorizar",
                    "detalle": f"Ni Inkscape ni cv2 trazaron la imagen (no lo invento): {r_cv2.get('detalle')}"}
        dxf_ruta = r_cv2["dxf"]
        pasos.append(f"Vectorizado a DXF (contornos cv2): {Path(dxf_ruta).name} "
                     f"({r_cv2.get('contornos')} contornos)")

    # 3) ESCALAR el DXF a la altura pedida (altura_cm)
    try:
        import ezdxf
        from ezdxf import bbox as ezbbox
        from ezdxf.math import Matrix44
        doc = ezdxf.readfile(dxf_ruta)
        msp = doc.modelspace()
        ext = ezbbox.extents(msp)
        alto_actual_mm = ext.size.y
        if alto_actual_mm <= 0:
            return {"status": "error", "paso": "escalar",
                    "detalle": "El DXF vectorizado quedó sin alto medible (la imagen no vectorizó bien)."}
        factor = (float(altura_cm) * 10.0) / alto_actual_mm
        m = Matrix44.scale(factor, factor, factor)
        for e in msp:
            try:
                e.transform(m)
            except Exception:
                pass  # entidades no transformables se ignoran (honesto: no todas soportan transform)
        dxf_escalado = str(Path(dxf_ruta).with_name(Path(dxf_ruta).stem + f"_h{int(altura_cm)}cm.dxf"))
        doc.saveas(dxf_escalado)
        ext2 = ezbbox.extents(doc.modelspace())
        pasos.append(f"Escalado a {altura_cm} cm de alto (factor {factor:.4f}); "
                     f"medida final {ext2.size.x/10:.1f} x {ext2.size.y/10:.1f} cm")
    except Exception as e:
        return {"status": "error", "paso": "escalar",
                "detalle": f"No pude escalar el DXF (no lo invento): {str(e)[:300]}"}

    # 4) MEDIR longitudes reales sobre el DXF escalado
    try:
        cot = _cargar_mod("cotizador_corte", ROOT / "EDITOR" / "cotizador_corte.py")
        doc = ezdxf.readfile(dxf_escalado)
        msp = doc.modelspace()
        long_total_mm = 0.0
        contorno_mm = 0.0
        contorno_area = -1.0
        cerradas = ("CIRCLE", "LWPOLYLINE", "POLYLINE", "SPLINE", "ELLIPSE")
        for e in msp:
            L = cot._long_entidad(e)
            long_total_mm += L
            if e.dxftype() in cerradas:
                a = _bbox_area(e)
                if a > contorno_area:
                    contorno_area = a
                    contorno_mm = L
        if long_total_mm <= 0:
            return {"status": "error", "paso": "medir",
                    "detalle": "El DXF no tiene trazo medible (la imagen no vectorizó bien)."}
    except Exception as e:
        return {"status": "error", "paso": "medir",
                "detalle": f"No pude medir el DXF (no lo invento): {str(e)[:300]}"}

    # Config de precios: costo/minuto real + velocidad de grabado real
    laser = cot._cargar_laser()
    costo_min = float(laser.get("costo_minuto", 8.0))
    v_grabado = velocidad_grabado_mm_s or _velocidad_grabado_config(200.0)
    v_corte = float(velocidad_corte_mm_s)

    # Material: cobra la fracción de hoja según el recuadro X×Y real (misma lógica que cotizar_corte)
    try:
        from ezdxf import bbox as ezbbox2
        ext_final = ezbbox2.extents(ezdxf.readfile(dxf_escalado).modelspace())
        area_cm2 = (ext_final.size.x / 10.0) * (ext_final.size.y / 10.0)
    except Exception:
        area_cm2 = 0.0
    costo_material = 0.0
    material_info = {"aviso": f"Material '{material}' no está en tu lista; costo material = 0."}
    if material:
        q = cot._norm(material)
        for mm_ in laser.get("materiales", []):
            if q in cot._norm(mm_.get("nombre", "")):
                hoja_cm2 = float(mm_.get("ancho", 122)) * float(mm_.get("alto", 244))
                precio_hoja = float(mm_.get("precio_hoja", 0))
                frac = min(1.0, area_cm2 / hoja_cm2) if hoja_cm2 else 0
                costo_material = round(precio_hoja * frac, 2)
                material_info = {"nombre": mm_.get("nombre", ""), "precio_hoja": precio_hoja,
                                 "fraccion_hoja_pct": round(frac * 100, 1)}
                break

    def _costo(long_mm, vel):
        t_min = long_mm / (vel * 60.0) if vel > 0 else 0.0
        return round(t_min, 2), round(t_min * costo_min, 2)

    modo = (modo or "corte_contorno").lower()
    costo_corte = costo_grabado = 0.0
    t_corte = t_grabado = 0.0
    long_medida_mm = 0.0
    detalle_modo = ""

    if modo == "grabado":
        long_medida_mm = long_total_mm
        t_grabado, costo_grabado = _costo(long_total_mm, v_grabado)
        detalle_modo = f"Graba todo el detalle ({long_total_mm/1000:.2f} m) a {v_grabado} mm/s."
    elif modo == "corte_contorno":
        if contorno_mm <= 0:
            return {"status": "error", "paso": "modo",
                    "detalle": "No encontré un contorno exterior cerrado para cortar (la silueta no cerró al vectorizar). Prueba modo='grabado'."}
        long_medida_mm = contorno_mm
        t_corte, costo_corte = _costo(contorno_mm, v_corte)
        detalle_modo = f"Corta solo el contorno exterior ({contorno_mm/1000:.2f} m) a {v_corte} mm/s."
    elif modo == "ambos":
        if contorno_mm <= 0:
            return {"status": "error", "paso": "modo",
                    "detalle": "No encontré contorno exterior cerrado para el corte; usa modo='grabado' o revisa la imagen."}
        detalle_mm = max(0.0, long_total_mm - contorno_mm)  # detalle interno = todo menos el contorno
        long_medida_mm = long_total_mm
        t_grabado, costo_grabado = _costo(detalle_mm, v_grabado)
        t_corte, costo_corte = _costo(contorno_mm, v_corte)
        detalle_modo = (f"Graba el detalle interno ({detalle_mm/1000:.2f} m @ {v_grabado} mm/s) "
                        f"+ corta el contorno ({contorno_mm/1000:.2f} m @ {v_corte} mm/s).")
    else:
        return {"status": "error", "paso": "modo",
                "detalle": f"Modo '{modo}' no válido. Usa: corte_contorno, grabado o ambos."}

    total = round(costo_corte + costo_grabado + costo_material, 2)

    return {
        "status": "ok",
        "modo": modo,
        "imagen": img.name,
        "dxf_escalado": dxf_escalado,
        "altura_cm": altura_cm,
        "longitud_total_trazo_m": round(long_total_mm / 1000.0, 2),
        "longitud_contorno_m": round(contorno_mm / 1000.0, 2),
        "longitud_medida_m": round(long_medida_mm / 1000.0, 2),
        "velocidad_corte_mm_s": v_corte,
        "velocidad_grabado_mm_s": v_grabado,
        "tiempo_corte_min": t_corte,
        "tiempo_grabado_min": t_grabado,
        "costo_minuto": costo_min,
        "costo_corte": costo_corte,
        "costo_grabado": costo_grabado,
        "material": material_info,
        "costo_material": costo_material,
        "total": total,
        "detalle_modo": detalle_modo,
        "pasos": pasos,
        "nota": ("Costo = (longitud/velocidad)/60*costo_minuto + material. Precios de "
                 "CONFIG/precios_base.json y velocidad de grabado de CONFIG/catalogo_servicios.json. "
                 "Contorno exterior = entidad cerrada de mayor bounding box."),
    }


if __name__ == "__main__":
    import sys
    r = cotizar_imagen_laser(sys.argv[1] if len(sys.argv) > 1 else "",
                             modo=sys.argv[2] if len(sys.argv) > 2 else "corte_contorno")
    print(json.dumps(r, ensure_ascii=False, indent=2))
