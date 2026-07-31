# -*- coding: utf-8 -*-
"""
AURORA · PRUEBAS DE REGRESIÓN DE BUGS REALES
=============================================
Cada prueba de este archivo corresponde a un bug REAL que se encontró y arregló
(auditoría Fase 3, 2026-07-28/29). No son pruebas inventadas para "tener
cobertura": cada una blinda un fallo que de verdad ocurrió y que costó tiempo,
dinero o credibilidad.

Objetivo: que ninguno de estos bugs pueda volver sin que nos enteremos.

Correr:  python -m pytest tests/ -v
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _cargar(nombre: str, ruta_rel: str):
    """Carga un módulo por ruta (igual que lo hace AURORA en producción)."""
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / ruta_rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# BUG 1 (CRÍTICO) — auto_reparacion podía BORRAR el 96% de consciencia.py
# Mandaba 6,000 caracteres al modelo pero reemplazaba el archivo COMPLETO.
# consciencia.py tiene 148,330 caracteres.
# ===========================================================================
class TestAutoReparacionNoDestruyeCodigo:

    def test_archivos_del_nucleo_estan_blindados(self):
        """El corazón de AURORA nunca se auto-repara sin revisión humana."""
        ar = _cargar("auto_reparacion", "CEREBRO/auto_reparacion.py")
        for critico in ("cerebro/consciencia.py", "core/aurora_server.py", "run_aurora.py"):
            assert critico in ar.ARCHIVOS_NUCLEO, (
                f"{critico} salió del blindaje: el auto-reparador podría destruirlo")

    def test_no_reescribe_lo_que_no_alcanza_a_ver(self):
        """Si el archivo no cabe completo en el contexto del modelo, se rechaza."""
        ar = _cargar("auto_reparacion", "CEREBRO/auto_reparacion.py")
        real = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert len(real) > ar.CHARS_AL_LLM, (
            "consciencia.py ya cabe completo — revisar si el candado sigue teniendo sentido")

    def test_rechaza_fixes_que_pierden_codigo(self):
        """Aunque compile, un fix que borra medio archivo NO se aplica."""
        ar = _cargar("auto_reparacion", "CEREBRO/auto_reparacion.py")
        assert 0 < ar.PERDIDA_LINEAS_MAX_PCT <= 30, (
            "El umbral de pérdida de líneas quedó peligrosamente permisivo")

    def test_limpia_el_markdown_del_modelo(self):
        """Sin esto la función NUNCA reparó nada: el ```python no compila."""
        ar = _cargar("auto_reparacion", "CEREBRO/auto_reparacion.py")
        con_markdown = "```python\ndef suma(a, b):\n    return a + b\n```"
        limpio = ar._limpiar_respuesta_llm(con_markdown)
        assert not limpio.startswith("```"), "Volvió el bug: el markdown no se limpia"
        assert "def suma" in limpio
        compile(limpio, "<test>", "exec")  # debe compilar de verdad

    def test_texto_sin_markdown_no_se_toca(self):
        ar = _cargar("auto_reparacion", "CEREBRO/auto_reparacion.py")
        codigo = "def x():\n    return 1"
        assert ar._limpiar_respuesta_llm(codigo) == codigo


# ===========================================================================
# BUG 2 — El cotizador usaba precios del NEGOCIO EQUIVOCADO
# Cotizar 50 tazas (Milens) usaba el catálogo de faros de ATF.
# ===========================================================================
class TestCotizadorNoConfundeNegocios:

    @pytest.mark.parametrize("pedido,esperado", [
        ("50 tazas ceramica 11oz sublimadas", "milens"),
        ("grabado laser en 20 agendas de vinipiel", "milens"),
        ("playeras poliester sublimadas, 30 piezas", "milens"),
        ("un par de faros led H4 premium para Honda Civic", "atf"),
        ("ojos de angel RGB con bluetooth", "atf"),
        ("retrofit completo con proyector bi-led aozoom", "atf"),
    ])
    def test_detecta_el_negocio_correcto(self, pedido, esperado):
        mc = _cargar("motor_cotizador", "MOTORES/motor_cotizador.py")
        assert mc._detectar_negocio(pedido) == esperado, (
            f"'{pedido}' se cotizaría con los precios del negocio equivocado")

    def test_usa_los_catalogos_reales_no_la_copia_vieja(self):
        """Antes tenía 4 productos ATF hardcodeados; los reales son ~98."""
        mc = _cargar("motor_cotizador", "MOTORES/motor_cotizador.py")
        atf, err_a = mc._catalogo_atf_real()
        assert atf, f"No se pudo leer el catálogo real de ATF: {err_a}"
        assert len(atf) > 50, f"El catálogo ATF trae solo {len(atf)} productos, se esperaban ~98"
        milens, err_m = mc._catalogo_milens_real()
        assert milens, f"No se pudo leer el catálogo real de MILENS: {err_m}"
        assert len(milens) > 50, f"El catálogo MILENS trae solo {len(milens)}, se esperaban ~73"

    def test_plural_y_singular_calzan(self):
        """Pedir '50 TAZAS' debe encontrar 'TAZA blanca 11oz'."""
        mc = _cargar("motor_cotizador", "MOTORES/motor_cotizador.py")
        milens, _ = mc._catalogo_milens_real()
        filtrado = mc._filtrar_catalogo(milens, "50 tazas blancas 11oz")
        nombres = " ".join(v.get("nombre", "").lower() for v in filtrado.values())
        assert "taza" in nombres, "Volvió el bug: pedir tazas no encuentra tazas"


# ===========================================================================
# BUG 3 — AURORA trataba a la familia de Anuar como clientes
# Su hija escribía "papá ya salí" y quedaba registrada como LEAD de ventas.
# ===========================================================================
class TestReconoceQuienEscribe:

    PERSONALES = [
        "papa ya sali de la escuela, pasas por mi?",
        "gordo, ya vienes?",
        "papito te quiero mucho",
        "que onda wey, ya llegaste?",
        "amorcito pasas por mi?",
        "a que hora llegas? ya comiste?",
    ]
    CLIENTES = [
        "buenas tardes, cuanto cuesta instalar lupas en un jetta?",
        "quiero cotizar 50 tazas sublimadas",
        "me chocaron, puede recolocar mi lupa?",
        "amigo, tiene faros para jetta?",     # 'amigo' NO debe leerse como personal
        "sr oiga tiene lupas?",
        "precio foco h4",
    ]

    @pytest.mark.parametrize("mensaje", PERSONALES)
    def test_a_la_familia_no_se_le_vende(self, mensaje):
        c = _cargar("contactos", "CONFIG/contactos.py")
        r = c.clasificar("5213399998888", mensaje)
        assert r.get("vender") is False, f"Le vendería a un familiar: '{mensaje}'"
        assert r.get("registrar_lead") is False, f"Registraría a un familiar como lead: '{mensaje}'"
        assert r.get("avisar_a_anuar") is True, f"No le avisaría a Anuar de: '{mensaje}'"

    @pytest.mark.parametrize("mensaje", CLIENTES)
    def test_al_cliente_si_se_le_atiende(self, mensaje):
        c = _cargar("contactos", "CONFIG/contactos.py")
        r = c.clasificar("5213399998888", mensaje)
        assert r.get("vender") is True, f"Perdería una venta real: '{mensaje}'"

    def test_la_intencion_de_compra_gana_al_tono(self):
        """Un compa que pregunta precio está COMPRANDO, no saludando."""
        c = _cargar("contactos", "CONFIG/contactos.py")
        assert c.clasificar("5213399998888", "wey cuanto cuestan las lupas?")["vender"] is True
        assert c.clasificar("5213399998888", "compa tienes focos h4?")["vender"] is True

    def test_nunca_inventa_un_nombre(self):
        c = _cargar("contactos", "CONFIG/contactos.py")
        assert c.nombre_conocido("5219999999999") == ""


# ===========================================================================
# BUG 4 — medidor_dxf NUNCA midió nada (usaba mal la librería)
# ===========================================================================
class TestMedidorDxfMideDeVerdad:

    def test_mide_un_rectangulo_conocido(self, tmp_path):
        ezdxf = pytest.importorskip("ezdxf")
        doc = ezdxf.new()
        doc.modelspace().add_lwpolyline([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)])
        archivo = tmp_path / "rect.dxf"
        doc.saveas(archivo)

        md = _cargar("medidor_dxf", "MOTORES_CUSTOM/medidor_dxf.py")
        r = md.ejecutar("medir", {"ruta": str(archivo)})
        assert r["status"] == "ok", f"No midió: {r}"
        assert abs(r["ancho"] - 10.0) < 0.01, f"Ancho incorrecto: {r['ancho']}"
        assert abs(r["alto"] - 5.0) < 0.01, f"Alto incorrecto: {r['alto']}"

    def test_archivo_inexistente_da_error_claro(self):
        md = _cargar("medidor_dxf", "MOTORES_CUSTOM/medidor_dxf.py")
        r = md.ejecutar("medir", {"ruta": r"C:\no_existe_xyz.dxf"})
        assert r["status"] == "error"

    def test_sin_ruta_no_revienta(self):
        md = _cargar("medidor_dxf", "MOTORES_CUSTOM/medidor_dxf.py")
        assert md.ejecutar("medir", {})["status"] == "error"
        assert md.ejecutar("medir", {"ruta": ""})["status"] == "error"


# ===========================================================================
# BUG 5 — Las rutas con ESPACIOS no se reconocían
# "Animal - Perro - Pitbull (Cabeza).pdf" y las imágenes de WhatsApp.
# ===========================================================================
class TestRutasConEspaciosYParentesis:

    RUTAS = [
        r"C:\Users\Administrador\Downloads\Animal - Perro - Pitbull (Cabeza).pdf",
        r"C:\Users\Administrador\Downloads\WhatsApp Image 2026-07-27 at 12.03.35 PM.jpeg",
        r"C:\ruta\sin_espacios.png",
    ]

    @pytest.mark.parametrize("ruta", RUTAS)
    def test_el_candado_de_corel_reconoce_la_ruta(self, ruta):
        import re
        patron = r"[A-Za-z]:\\[^\r\n]+?\.(?:png|jpg|jpeg|bmp|gif|tif|tiff|pdf|cdr|ai)"
        assert re.findall(patron, f"corel abre {ruta}", re.I), f"No reconoció: {ruta}"

    @pytest.mark.parametrize("ruta", RUTAS)
    def test_el_candado_de_dxf_reconoce_la_ruta(self, ruta):
        import re
        patron = r"[A-Za-z]:\\[^\r\n]+?\.(?:svg|pdf|ai|eps|cdr|dxf|png|jpg|jpeg)"
        if Path(ruta).suffix.lower() in (".pdf", ".png", ".jpeg", ".jpg"):
            assert re.search(patron, f"convierte a dxf {ruta}", re.I), f"No reconoció: {ruta}"

    def test_no_quedan_regex_viejos_en_codigo_vivo(self):
        """El patrón [^\\s] excluye espacios — causó los dos bugs. No debe volver."""
        for archivo in ("CEREBRO/consciencia.py",):
            texto = (RAIZ / archivo).read_text(encoding="utf-8")
            assert r'[A-Za-z]:\\[^\s' not in texto, (
                f"Volvió el regex que rompe con rutas con espacios en {archivo}")


# ===========================================================================
# BUG 6 — pronostico_embudo SIEMPRE daba $0
# crear_lead nunca guardaba el valor estimado.
# ===========================================================================
class TestPronosticoDeVentas:

    def test_crear_lead_acepta_valor_estimado(self):
        import inspect
        oc = _cargar("oracle_core", "ORACLE/oracle_core.py")
        params = inspect.signature(oc.crear_lead).parameters
        assert "valor_estimado" in params, (
            "Volvió el bug: sin este parámetro el pronóstico del embudo siempre da $0")

    def test_existe_forma_de_corregir_el_valor_despues(self):
        oc = _cargar("oracle_core", "ORACLE/oracle_core.py")
        assert hasattr(oc, "actualizar_lead_valor")


# ===========================================================================
# BUG 7 — El generador de cajas decía medidas ENGAÑOSAS ("80x50x40cm... mm")
# y reportaba OK aunque el DXF no se generara.
# ===========================================================================
class TestCajasYDxfHonestos:

    def test_no_queda_la_etiqueta_enganosa(self):
        """Se revisa el CÓDIGO EJECUTABLE, no los comentarios (que sí mencionan
        el texto viejo a propósito, para documentar qué se arregló)."""
        import ast
        arbol = ast.parse((RAIZ / "TALLER" / "taller_core.py").read_text(encoding="utf-8"))
        textos = [n.value for n in ast.walk(arbol)
                  if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        # Las f-strings quedan partidas en trozos; se revisa cada uno.
        for t in textos:
            assert "cm... mm" not in t, "Volvió la etiqueta de unidades engañosa"
        fuente = (RAIZ / "TALLER" / "taller_core.py").read_text(encoding="utf-8")
        assert "medidas_mm" in fuente and "medidas_cm" in fuente

    def test_un_dxf_vacio_no_se_reporta_como_exito(self, tmp_path):
        ezdxf = pytest.importorskip("ezdxf")
        vacio = tmp_path / "vacio.dxf"
        ezdxf.new().saveas(vacio)
        tc = _cargar("taller_core", "TALLER/taller_core.py")
        assert tc._dxf_tiene_contenido(vacio) == 0, (
            "Un DXF vacío debe detectarse: no sirve para cortar")

    def test_detecta_pdf_que_solo_trae_imagen(self):
        """El PDF del pitbull: 0 vectores, 1 imagen -> hay que vectorizar, no convertir."""
        tc = _cargar("taller_core", "TALLER/taller_core.py")
        assert hasattr(tc, "pdf_tiene_vectores")
        assert hasattr(tc, "pdf_pagina_a_imagen"), "Sin esto no se pueden usar PDFs de varias páginas"


# ===========================================================================
# BUG 8 — La capacidad OFFLINE estaba muerta (pedía un modelo inexistente)
# ===========================================================================
class TestRespaldoSinInternet:

    def test_no_hay_modelo_hardcodeado_inexistente(self):
        sdk = _cargar("aurora_sdk_manager", "CORE/aurora_sdk_manager.py")
        assert hasattr(sdk.AuroraSDKManager, "PREFERENCIA_OLLAMA")
        pref = sdk.AuroraSDKManager.PREFERENCIA_OLLAMA
        assert pref[0] != "mistral", "Volvió el modelo que no está instalado"

    def test_prefiere_modelos_ligeros_por_la_ram(self):
        """En una PC de 7.2 GB un modelo 7B se pasa de 120s y no contesta."""
        sdk = _cargar("aurora_sdk_manager", "CORE/aurora_sdk_manager.py")
        pref = list(sdk.AuroraSDKManager.PREFERENCIA_OLLAMA)
        assert "7b" not in pref[0].lower(), (
            f"El primero de la lista ({pref[0]}) es pesado para esta máquina")


# ===========================================================================
# BUG 9 — Buscar un archivo inexistente trababa el chat +2 MINUTOS
# ===========================================================================
class TestBusquedaDeArchivosRapida:

    def test_ignora_las_carpetas_pesadas(self):
        acc = _cargar("acciones_sistema", "CEREBRO/acciones_sistema.py")
        ignoradas = " ".join(acc._CARPETAS_IGNORADAS)
        for pesada in (".git", "SUPER_MARKETING_SYSTEM", "site-packages"):
            assert pesada in ignoradas, (
                f"Sin ignorar {pesada}, una búsqueda sin resultado tarda minutos")


# ===========================================================================
# BUG 10 — AURORA inventaba capacidades al describirse
# ===========================================================================
class TestSeDescribeConDatosReales:

    @pytest.mark.parametrize("frase", [
        "podrias autodescribirte a detalle",
        "describete",
        "que puedes hacer",
        "cuantas herramientas tienes",
        "quien eres",
    ])
    def test_reconoce_las_frases_de_autodescripcion(self, frase):
        """Si no las reconoce, cae en el motor genérico que INVENTA capacidades.

        Se usa la FUNCIÓN REAL del sistema, no un análisis del texto del archivo:
        leer el código con expresiones regulares se rompía con los paréntesis de
        los comentarios y daba falsos fallos.
        """
        import ast
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        arbol = ast.parse(fuente)
        disparadores = None
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Assign):
                for destino in nodo.targets:
                    if isinstance(destino, ast.Name) and destino.id == "_ACERCA_DE_TRIGGERS":
                        disparadores = [e.value for e in nodo.value.elts
                                        if isinstance(e, ast.Constant)]
        assert disparadores, "No encontré la lista de frases de autodescripción"
        assert any(d in frase for d in disparadores), (
            f"'{frase}' no dispara la autodescripción real — inventaría capacidades")


# ===========================================================================
# BUG 11 — motor_analisis FINGÍA haber ejecutado acciones
# Dijo "CorelDRAW: PDF cargado... Vectorización finalizada" sin hacer nada.
# ===========================================================================
class TestNoFingeAcciones:

    def test_tiene_prohibido_fingir_que_ejecuto_algo(self):
        texto = (RAIZ / "MOTORES" / "motor_analisis.py").read_text(encoding="utf-8")
        assert "NO TIENES MANOS" in texto.upper(), (
            "Volvió el riesgo de que invente que ejecutó una acción")
        assert "vectorizado_con_coreldraw" in texto, (
            "Se perdió la referencia al caso real que enseña qué NO hacer")


# ===========================================================================
# BUG 12 (RAÍZ) — AURORA inventaba: fingía acciones, comandos y archivos
# 7 casos reales el 29-30 jul. Causa común: cuando la frase no calzaba con un
# candado, caía a un modelo sin acceso al sistema que respondía igual.
# El validador es CÓDIGO: un modelo chico no lo puede ignorar como al prompt.
# ===========================================================================
class TestNoPuedeInventar:

    @staticmethod
    def _claves():
        rh = _cargar("registro_herramientas", "CEREBRO/registro_herramientas.py")
        return set(rh.descubrir())

    def test_atrapa_que_fingio_que_corel_trabajo(self):
        """El invento textual real del 2026-07-29."""
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        texto = ("CorelDRAW: PDF cargado correctamente\n"
                 "CorelDRAW: Vectorizacion finalizada\n"
                 "resultado: vectorizado_con_coreldraw.pdf")
        _, inf = vh.revisar(texto, motores_usados=["motor_analisis"],
                            registro_claves=self._claves())
        assert inf["corregida"], "Volvería a fingir que Corel trabajó"
        assert inf["afirmo_accion_sin_hacerla"]

    def test_atrapa_comandos_inventados(self):
        """El 'MANUAL MAESTRO' real traía 6 de 8 comandos falsos."""
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        texto = "Ejecuta AGENDA/agrega_usuario y luego CORE/evalua_expresion"
        _, inf = vh.revisar(texto, motores_usados=["motor_analisis"],
                            registro_claves=self._claves())
        assert "AGENDA/agrega_usuario" in inf["comandos_inventados"]
        assert "CORE/evalua_expresion" in inf["comandos_inventados"]

    def test_atrapa_archivos_inventados(self):
        """El 'kit de configuración' real mandaba usar 3 .bat inexistentes."""
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        texto = "Si se congela ejecuta REINICIAR_NGROK.bat o NEXUS.bat"
        _, inf = vh.revisar(texto, motores_usados=["motor_analisis"],
                            registro_claves=self._claves())
        assert "REINICIAR_NGROK.bat" in inf["archivos_inexistentes"]

    def test_no_estorba_a_una_ejecucion_real(self):
        """Un candado que SÍ ejecutó no debe recibir advertencias."""
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        texto = "Documento real cerrado sin guardar: 'Sin titulo-1'."
        _, inf = vh.revisar(texto, motores_usados=["motor_corel"],
                            registro_claves=self._claves())
        assert not inf["corregida"], "Molestaría en respuestas legítimas"

    def test_no_marca_un_comando_que_si_existe(self):
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        texto = "Puedes usar MARKETING/catalogo_compartible:generar_catalogo_pdf"
        _, inf = vh.revisar(texto, motores_usados=["motor_analisis"],
                            registro_claves=self._claves())
        assert not inf["comandos_inventados"]

    def test_una_promesa_no_es_una_mentira(self):
        """'Voy a hacerlo' es válido; 'ya lo hice' sin hacerlo no."""
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        _, inf = vh.revisar("Voy a convertirlo en cuanto me des la ruta.",
                            motores_usados=["motor_analisis"],
                            registro_claves=self._claves())
        assert not inf["corregida"]

    def test_esta_conectado_al_punto_unico_de_salida(self):
        """De nada sirve el validador si no se llama donde salen TODAS las respuestas."""
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert "validador_honestidad" in fuente, (
            "El validador existe pero no está conectado: las respuestas saldrían sin revisar")


# ===========================================================================
# BUG 13 — La navegación web no se activaba con lenguaje natural
# ===========================================================================
class TestBusquedaWebConLenguajeNatural:

    @pytest.mark.parametrize("frase", [
        "investiga el precio de faros led h4",
        "buscame proveedores de acrilico",
        "que dicen de los proyectores aozoom",
        "compara precios de termos",
        "busca en internet cuanto cuesta",
    ])
    def test_reconoce_como_se_pide_de_verdad(self, frase):
        import ast
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        disparadores = None
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.Assign):
                for d in nodo.targets:
                    if isinstance(d, ast.Name) and d.id == "_BUSQUEDA_WEB_TRIGGERS":
                        disparadores = [e.value for e in nodo.value.elts
                                        if isinstance(e, ast.Constant)]
        assert disparadores, "No encontré la lista de frases de búsqueda web"
        assert any(t in frase for t in disparadores), (
            f"'{frase}' no activa la búsqueda web — respondería inventando")


# ===========================================================================
# BUG 14 — El enrutador inventaba la INTENCIÓN, no solo el dato
# A "usa coreldraw para vectorizar el archivo que tengo abierto" respondió
# proponiendo 'preparar_para_lona'. Nadie habló de lonas. La herramienta SÍ
# existe, así que el validador de honestidad la dejaba pasar: este es el hueco.
# Regla de Anuar: "prefiero que se niegue o que exija la información real,
# pero que no responda invenciones".
# ===========================================================================
class TestRouterNoInventaLaIntencion:

    def test_descarta_la_herramienta_si_faltan_TODOS_sus_datos(self):
        """Que falten todos los requeridos no es 'me falta un dato' —
        es que la herramienta está mal elegida."""
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert "len(faltantes) == len(requeridos)" in fuente, (
            "Volvería a proponer una herramienta que no viene al caso")

    def test_no_nombra_la_herramienta_equivocada(self):
        """Nombrarla es peor que callar: el usuario cree que existe esa capacidad."""
        import ast
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        arbol = ast.parse(fuente)
        # La respuesta del descarte no debe interpolar la clave de la herramienta
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                if "No tengo una herramienta que haga eso" in nodo.value:
                    assert "{clave}" not in nodo.value
                    return
        pytest.fail("No encontré el mensaje de descarte del enrutador")
