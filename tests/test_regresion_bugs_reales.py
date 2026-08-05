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


# ===========================================================================
# BUG 15 — El validador daba avisos FALSOS ("PDF/CDR" no es un comando)
# Marcaba formatos de archivo como comandos inventados. Un candado que hace
# ruido se ignora, y deja de servir para lo que existe.
# ===========================================================================
class TestValidadorNoHaceRuido:

    @staticmethod
    def _claves():
        rh = _cargar("registro_herramientas", "CEREBRO/registro_herramientas.py")
        return set(rh.descubrir())

    @pytest.mark.parametrize("texto", [
        "Puedo abrir PDF/CDR/AI dentro de Corel",
        "Exportar a PNG/JPG no funciona, usa PDF",
        "Formatos soportados: SVG/DXF y EPS/AI",
    ])
    def test_los_formatos_de_archivo_no_son_comandos(self, texto):
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        _, inf = vh.revisar(texto, motores_usados=["motor_corel"],
                            registro_claves=self._claves())
        assert not inf["comandos_inventados"], (
            f"Aviso falso sobre {inf['comandos_inventados']} — el candado hace ruido")

    def test_pero_sigue_atrapando_los_inventos_de_verdad(self):
        """El arreglo del ruido no debe apagar la detección real."""
        vh = _cargar("validador_honestidad", "CEREBRO/validador_honestidad.py")
        _, inf = vh.revisar("Ejecuta AGENDA/agrega_usuario para darlo de alta",
                            motores_usados=["motor_analisis"],
                            registro_claves=self._claves())
        assert "AGENDA/agrega_usuario" in inf["comandos_inventados"]


# ===========================================================================
# BUG 16 — Mandar solo una ruta provocaba una NEGACIÓN FALSA
# Tras pedir "abre esta imagen en corel", mandar solo C:\...\balon.jpg caía en
# motor_analisis: "no puedo abrir archivos en la PC, pídele a Anuar que lo
# haga". Mentira (AURORA sí abre en Corel) y encima le decía a Anuar que le
# pidiera a Anuar.
# ===========================================================================
class TestRutaSolaNoNiegaFalsamente:

    @pytest.mark.parametrize("msg", [
        r'"C:\Users\Administrador\Downloads\balon.jpg"',
        r"C:\Users\Administrador\Downloads\balon.jpg",
        r"  C:\ruta con espacios\archivo.pdf  ",
    ])
    def test_reconoce_una_ruta_sola(self, msg):
        import importlib.util, sys as _s
        spec = importlib.util.spec_from_file_location("_c", RAIZ / "CEREBRO" / "consciencia.py")
        # Se lee el módulo sin ejecutarlo: importar consciencia levanta medio sistema.
        import ast, re as _re
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.Assign):
                for d in nodo.targets:
                    if isinstance(d, ast.Name) and d.id == "_RE_RUTA_SOLA":
                        patron = nodo.value.args[0].value
                        assert _re.match(patron, msg.strip()), f"No reconoce: {msg}"
                        return
        pytest.fail("No encontré _RE_RUTA_SOLA")

    def test_una_frase_normal_no_es_una_ruta_sola(self):
        import ast, re as _re
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.Assign):
                for d in nodo.targets:
                    if isinstance(d, ast.Name) and d.id == "_RE_RUTA_SOLA":
                        patron = nodo.value.args[0].value
                        for frase in (r"corel abre C:\x\y.jpg", "cuanto vendi este mes"):
                            assert not _re.match(patron, frase), f"Falso positivo: {frase}"
                        return
        pytest.fail("No encontré _RE_RUTA_SOLA")

    def test_el_candado_va_primero_y_esta_conectado(self):
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert '("ruta_sola",' in fuente, "El candado no está registrado"
        assert "_ruta_sola_real" in fuente, "Falta el ejecutor"
        i_ruta = fuente.index('("ruta_sola",')
        i_corel = fuente.index('("corel",')
        assert i_ruta < i_corel, "ruta_sola debe ir antes que los demás candados"


# ===========================================================================
# BUG 17 — El candado ruta_sola recibía session_id vacío
# El pipeline llama getattr(self, metodo)(mensaje): SOLO el mensaje. Los
# candados que necesitan la sesión llevan su propia rama. Sin ella,
# _ruta_sola_real leía el historial de una sesión "" (siempre vacía) y nunca
# completaba la petición anterior. Tres hipótesis fallaron antes de ver esto:
# el problema no era dónde se guardaba el dato, era que no sabía de qué sesión.
# ===========================================================================
class TestCandadosQueNecesitanLaSesionLaReciben:

    def test_ruta_sola_recibe_session_id(self):
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert '_ruta_sola_real(mensaje, session_id=session_id' in fuente, (
            "Sin su rama en el pipeline, ruta_sola recibe session_id='' y el "
            "historial que lee siempre está vacío")

    def test_lee_del_historial_que_si_persiste(self):
        """_memoria_corto persiste entre mensajes; un dict nuevo no hacía falta."""
        import ast
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        # Se recorta la función COMPLETA con AST, no una ventana de N caracteres:
        # la primera versión miraba 2,500 caracteres fijos y se puso en rojo sola
        # cuando la función creció al manejar rutas sin extensión. Una prueba que
        # se rompe porque el código creció no protege nada, solo estorba.
        cuerpo = ""
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.AsyncFunctionDef) and nodo.name == "_ruta_sola_real":
                cuerpo = ast.get_source_segment(fuente, nodo) or ""
                break
        assert cuerpo, "No encontré _ruta_sola_real"
        assert "_memoria_corto" in cuerpo, "Debe leer del historial de sesión real"
        assert "_ultima_peticion" not in fuente, (
            "Quedó el mecanismo viejo que nunca funcionó — código huérfano")


# ===========================================================================
# BUG 18 — Escrituras simultáneas en las bases del taller
# El 27-jul aparecieron en el log: "UNIQUE constraint failed: ordenes.folio" y
# "database is locked". Se arreglaron en crear_orden y _con(), pero init_db()
# quedó sin timeout ni WAL, y editar_orden leía y escribía sin transacción.
#
# Lo peor no era que tronara: editar sin transacción NO truena y NO queda en el
# log — dos ediciones a la vez y la segunda pisa a la primera. Un anticipo
# cobrado podía desaparecer del saldo sin dejar rastro.
# Anuar y Rocío usan el panel al mismo tiempo: no es hipotético.
# ===========================================================================
class TestBasesAguantanDosPersonasALaVez:

    def test_todas_las_conexiones_del_taller_llevan_timeout(self):
        """Sin timeout se rinden a los 5 s por defecto: eso es el 'database is locked'."""
        fuente = (RAIZ / "TALLER" / "ordenes_taller.py").read_text(encoding="utf-8")
        conexiones = [l for l in fuente.splitlines() if "sqlite3.connect(" in l]
        assert conexiones, "No encontré ninguna conexión — ¿cambió el archivo?"
        for linea in conexiones:
            assert "timeout=" in linea, f"Conexión sin timeout: {linea.strip()}"

    def test_el_taller_usa_WAL(self):
        """Sin WAL, un lector bloquea a un escritor."""
        fuente = (RAIZ / "TALLER" / "ordenes_taller.py").read_text(encoding="utf-8")
        assert fuente.count("journal_mode=WAL") >= 2, (
            "init_db() o _con() se quedó sin WAL")

    def test_editar_orden_es_una_sola_transaccion(self):
        """Leer y escribir por separado deja pasar un 'lost update' silencioso:
        el anticipo cobrado desaparece y nadie se entera."""
        fuente = (RAIZ / "TALLER" / "ordenes_taller.py").read_text(encoding="utf-8")
        i = fuente.index("def editar_orden")
        cuerpo = fuente[i:i + 3000]
        assert "BEGIN IMMEDIATE" in cuerpo, (
            "editar_orden volvió a leer y escribir sin transacción")
        assert "rollback" in cuerpo, (
            "Si se sale a media transacción sin rollback, la base queda bloqueada")

    def test_oracle_no_repite_el_error_del_taller(self):
        """oracle.db guarda los LEADS. Estaba en la misma configuración que
        rompió el taller: sin timeout y sin WAL."""
        fuente = (RAIZ / "ORACLE" / "oracle_core.py").read_text(encoding="utf-8")
        i = fuente.index("def _conn")
        cuerpo = fuente[i:i + 900]
        assert "timeout=" in cuerpo, "oracle_core._conn() sin timeout"
        assert "journal_mode=WAL" in cuerpo, "oracle_core._conn() sin WAL"

    def test_dos_ordenes_al_mismo_tiempo_no_chocan(self):
        """La prueba de verdad: dos hilos creando órdenes a la vez, como cuando
        Anuar y Rocío usan el panel al mismo tiempo."""
        import concurrent.futures as cf
        ot = _cargar("ordenes_taller", "TALLER/ordenes_taller.py")

        def crear(n):
            return ot.crear_orden({
                "solicitante": "Anuar", "cliente": f"ConcurrenciaTest{n}",
                "trabajo": "prueba de concurrencia", "piezas": 1,
                "valor_total": 100, "anticipo": 0,
            })

        with cf.ThreadPoolExecutor(max_workers=5) as ex:
            resultados = list(ex.map(crear, range(5)))

        ok = [r for r in resultados if str(r.get("status", "")).lower() in ("ok", "exito", "éxito")]
        assert len(ok) == 5, f"Solo {len(ok)}/5 órdenes simultáneas se crearon: {resultados}"
        folios = [r.get("folio") for r in ok]
        assert len(set(folios)) == 5, f"Folios repetidos: {folios}"

        # Limpieza: no dejar basura en la base real de Anuar.
        con = ot._con()
        con.execute("DELETE FROM ordenes WHERE cliente LIKE 'ConcurrenciaTest%'")
        con.commit()
        con.close()


# ===========================================================================
# BUG 19 — AURORA no aprendía cómo habla su dueño
# Idea de Anuar (2026-08-02): "también podría ser que aprendiera del usuario
# cómo es que se expresa, tal cual tú lo haces; así no tendrías que inventar el
# fix, solo copiarlo".
#
# Durante dos días el arreglo fue siempre el mismo: él escribía algo, no se
# entendía, y se agregaba su frase a una lista a mano. Eso no se acaba nunca.
# Medido en vivo: "echale un ojo a las cuentas del changarro" pasó de 25.4 s
# inventando en motor_analisis, a 0.6 s con el dato real. Sin tocar una lista.
# ===========================================================================
class TestAprendeComoHablaSuDuenio:

    @staticmethod
    def _mod():
        return _cargar("aprende_del_usuario", "CEREBRO/aprende_del_usuario.py")

    def test_aprende_aunque_las_frases_no_compartan_palabras(self):
        """La primera versión exigía que las dos frases compartieran una palabra
        y por eso NUNCA aprendía: una reformulación de verdad casi nunca repite
        las palabras — precisamente por eso es una reformulación."""
        import time
        a = self._mod()
        ahora = time.time()
        a.registrar_fallo("prueba_regresion", "echale un ojo a las cuentas del changarro", ahora)
        r = a.registrar_exito("prueba_regresion", "como va la contabilidad",
                              "negocio_real", ahora + 5)
        try:
            assert r, "No aprendió: dos frases sin palabras en común son el caso normal"
            assert r["herramienta"] == "negocio_real"
            hallado = a.buscar("echale un ojo a las cuentas del changarro")
            assert hallado and hallado["herramienta"] == "negocio_real"
        finally:
            a.olvidar("changarro")      # no dejar basura en el archivo real

    def test_no_aprende_si_nada_ejecuto(self):
        """Sin un éxito real detrás, no hay nada que aprender."""
        import time
        a = self._mod()
        antes = len(a.listar())
        a.registrar_fallo("p2", "una frase cualquiera que no funciono", time.time())
        assert len(a.listar()) == antes

    def test_no_aprende_si_paso_mucho_tiempo(self):
        """Dos mensajes seguidos son una reformulación; con media hora de por
        medio son dos temas distintos."""
        import time
        a = self._mod()
        ahora = time.time()
        a.registrar_fallo("p3", "algo que fallo hace rato", ahora)
        r = a.registrar_exito("p3", "otra cosa distinta", "agenda",
                              ahora + a.SEGUNDOS_MAX_ENTRE_INTENTOS + 60)
        assert r is None, "Aprendió de dos mensajes sin relación"

    def test_no_confunde_frases_distintas(self):
        """Enrutar mal por un alias flojo es peor que no tener alias."""
        a = self._mod()
        for ajena in ("que hora es", "hola como estas", "gracias"):
            hallado = a.buscar(ajena)
            if hallado:
                assert hallado.get("parecido", 0) >= 0.6, (
                    f"'{ajena}' calzó con un alias flojo: {hallado}")

    def test_anuar_puede_ver_y_borrar(self):
        """Un sistema que aprende solo tiene que poder mirarse y deshacerse."""
        a = self._mod()
        assert callable(a.listar) and callable(a.olvidar) and callable(a.olvidar_todo)
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert "_es_ver_aprendizaje" in fuente, (
            "Sin el candado para verlo, aprende a espaldas de Anuar")

    def test_el_perfil_de_anuar_viene_precargado(self):
        """Su versión trae sus modismos de fábrica; la del demo arranca vacía y
        aprende del cliente."""
        a = self._mod()
        precargadas = [i for i in a.listar() if i.get("precargado")]
        assert len(precargadas) >= 5, (
            "Se perdió el perfil de Anuar (coreldrau, corte de caja, wats...)")


# ===========================================================================
# BUG 21 — "extrae el mapa de bits": faltaba el VERBO, y por eso mintió
# Caso real 2026-08-03 en el chat de Anuar. Importó trailer.jpg a Corel (bien,
# motor_corel, real) y en el siguiente mensaje pidió "ahora extrae el mapa de
# bits". Ningún candado lo agarró: _es_comando_corel exige nombrar "corel" Y
# una acción conocida, y "extrae" ni siquiera estaba en _VERBOS_DE_ACCION. Al
# no contar como intención operativa, contestó motor_analisis — un modelo sin
# manos — con "no puedo ejecutar acciones físicas en la PC, hazlo tú manualmente
# en Corel". DOS MENSAJES después de haber importado la imagen él mismo.
#
# El arreglo NO fue agregar "extrae" a la lista: eso deja el próximo hueco
# abierto. Los verbos ahora se leen del REGISTRO REAL de las 535 herramientas,
# así que una herramienta nueva trae su verbo sola.
# ===========================================================================
class TestVerbosSalenDelRegistroNoDeUnaListaAMano:

    def _fuente(self):
        return (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")

    @pytest.mark.parametrize("frase", [
        "ahora extrae el mapa de bits",
        "extrae el mapa de bits",
        "rasteriza el documento",
        "convierte a mapa de bits",
    ])
    def test_el_caso_real_llega_a_corel(self, frase):
        """Las frases exactas que mintieron. Deben terminar en motor_corel."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc"] = mod
        spec.loader.exec_module(mod)
        assert mod._es_comando_corel(frase), (
            f"'{frase}' no llega a Corel: vuelve a caer en motor_analisis")

    def test_extrae_es_intencion_operativa(self):
        """Si no es operativa, el corte router-first no la protege y miente."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc2", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc2"] = mod
        spec.loader.exec_module(mod)
        for frase in ("extrae el mapa de bits", "sacale el dibujo lineal",
                      "quiero extraer el texto", "pasalo a corte", "voltea los videos"):
            assert mod._es_intencion_operativa(frase), f"'{frase}' no cuenta como operativa"

    def test_platicar_sigue_sin_ser_operativo(self):
        """Ampliar los verbos no debe volver operativa una plática normal."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc3", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc3"] = mod
        spec.loader.exec_module(mod)
        for frase in ("gracias, muy amable", "como estas", "que opinas del clima"):
            assert not mod._es_intencion_operativa(frase), f"Falso positivo: '{frase}'"

    def test_los_verbos_se_leen_del_registro_real(self):
        """La defensa de fondo: la lista a mano SIEMPRE se queda corta."""
        fuente = self._fuente()
        assert "_verbos_del_registro" in fuente, (
            "Se volvió a una lista de verbos escrita a mano: el próximo verbo "
            "que nadie previó vuelve a caer en motor_analisis y a mentir")
        assert "_VERBOS_PLOMERIA" in fuente, (
            "Sin filtro, 'get'/'init'/'main' entran como verbos de Anuar")

    def test_corel_se_reconoce_sin_nombrarlo(self):
        """'mapa de bits' solo se dice en Corel: exigir la palabra 'corel'
        rompía la conversación en cuanto él dejaba de repetirla."""
        fuente = self._fuente()
        assert "_COREL_SIN_NOMBRARLO" in fuente, "Falta el vocabulario propio de Corel"

    def test_no_promete_exportar_bitmap_que_esta_roto(self):
        """exportar_bitmap NO funciona por pywin32. Prometerlo sería mentir."""
        fuente = self._fuente()
        i = fuente.index("_COREL_SIN_NOMBRARLO")
        bloque = fuente[i:i + 12000]
        assert "pywin32" in bloque or "PDF" in bloque, (
            "La respuesta de mapa de bits debe decir que PNG/JPG no sale y PDF sí")


# ===========================================================================
# BUG 22 — "✅ Abierto real" de un archivo que NUNCA se abrió
# Caso real 2026-08-03. Anuar pidió abrir
# "...\Downloads\Bart_simpson\Bart_simpson" y convertirlo a DXF. AURORA
# contestó "✅ Abierto real en Corel: 'Sin título-1.cdr'" — el documento VACÍO
# que ya estaba en pantalla. Dos fallas encadenadas:
#   1. Path.exists() da True para CARPETAS, y eso era una carpeta (quedó
#      anidada al descomprimir Bart_simpson.rar). Pasó el filtro.
#   2. Al abrir, se leía doc.Name SIN compararlo con lo pedido. Corel devuelve
#      el documento activo cuando la apertura falla, así que se cantó éxito
#      de algo que no ocurrió.
# Es exactamente el tipo de mentira que los candados existen para impedir, solo
# que aquí venía desde el motor, por debajo del validador.
# ===========================================================================
class TestCorelNoCantaExitoDeLoQueNoAbrio:

    def _fuente(self):
        return (RAIZ / "EDITOR" / "corel_core.py").read_text(encoding="utf-8")

    def test_una_carpeta_no_pasa_por_archivo(self):
        fuente = self._fuente()
        i = fuente.index("def abrir_documento")
        bloque = fuente[i:i + 2600]
        assert "is_dir()" in bloque, (
            "exists() da True para carpetas: sin is_dir() se le manda una "
            "carpeta a Corel y se reporta abierta")
        assert "es_carpeta" in bloque, "Debe decir que es una carpeta, no fallar en silencio"

    def test_compara_lo_abierto_contra_lo_pedido(self):
        """La defensa de fondo: si el documento activo no es el que se pidió,
        NO se cuenta como hecho."""
        fuente = self._fuente()
        i = fuente.index("def abrir_documento")
        bloque = fuente[i:i + 2600]
        assert "no_abrio" in bloque, (
            "Sin esta comparación, Corel devuelve el documento que ya estaba "
            "y AURORA lo reporta como abierto: la mentira del 2026-08-03")
        assert "origen.stem.lower()" in bloque, "Falta comparar el nombre real"

    def test_la_carpeta_del_caso_real_se_detecta(self):
        """Se prueba con la ruta real que falló, sin necesitar Corel abierto."""
        from pathlib import Path as _P
        ruta = _P(r"C:\Users\Administrador\Downloads\Bart_simpson\Bart_simpson")
        if not ruta.exists():
            pytest.skip("La carpeta del caso real ya no está en este disco")
        assert ruta.is_dir(), "El caso real era una CARPETA con .pdo adentro"


# ===========================================================================
# BUG 23 — El cotizador cotizó 100 PLAYERAS cuando se pidió papel de MercadoLibre
# Caso real 2026-08-04. Anuar escribió "busca en mercado libre el mejor precio
# de 100 hojas de papel adhesivo para impresora laser". El candado de cotizar
# vio "precio" + "100" y se lanzó: devolvió 100 playeras + 100 boxers + 100
# cajas MDF por $75,000. El mensaje decía DÓNDE buscar y aun así ganó, porque
# cotizar va antes que busqueda_web en la lista de candados.
#
# La raíz es conceptual: el cotizador es para VENDER, no para COMPRAR. Si se
# pregunta cuánto cuesta algo AFUERA (MercadoLibre, Amazon, un proveedor), ese
# candado no tiene nada que hacer ahí.
#
# Y la otra mitad: "encuentra el mejor precio por 100 hojas y dame el link" no
# la agarraba NINGÚN candado — se iba a motor_analisis.
# ===========================================================================
class TestCotizadorNoSeMeteEnComprasDeAfuera:

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc23", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc23"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _candado(self, mod, frase):
        for _n, trig, _m, motor in mod._CANDADOS:
            try:
                if trig(frase):
                    return motor
            except TypeError:
                pass
        return ""

    @pytest.mark.parametrize("frase", [
        "busca en mercado libre el mejor precio de 100 hojas de papel adesivo",
        "encuentra el mejor precio por 100 hojas y dame el link",
        "donde compro papel adhesivo mas barato",
        "donde venden vinil textil",
    ])
    def test_comprar_afuera_va_a_la_web(self, frase):
        """Preguntar dónde comprar NO es pedir una cotización del taller."""
        mod = self._mod()
        assert self._candado(mod, frase) == "web_search", (
            f"'{frase}' no llega a la búsqueda web: puede volver a cotizar "
            "100 playeras por $75,000")

    @pytest.mark.parametrize("frase,esperado", [
        ("cuanto cuestan 100 playeras", "cotizador"),
        ("cotizame 20 termos", "cotizador"),
        ("cuanto cuesta el faro aozoom x5", "cotizador"),
        ("cuanto sale la instalacion de lupas", "servicios_atf"),
    ])
    def test_cotizar_de_verdad_sigue_funcionando(self, frase, esperado):
        """El arreglo no debe romper las cotizaciones reales, que es lo que
        más dinero trae."""
        mod = self._mod()
        assert self._candado(mod, frase) == esperado, f"Se rompió: '{frase}'"

    def test_existe_la_separacion_vender_vs_comprar(self):
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert "_es_compra_afuera" in fuente, (
            "Sin separar comprar de vender, el cotizador vuelve a secuestrar "
            "cualquier mensaje que traiga la palabra precio y un número")
        assert "_TIENDAS_DE_AFUERA" in fuente, "Falta la lista de tiendas externas"


# ===========================================================================
# MEJORA 24 — Aprender a la PRIMERA, sin cobrarle un fallo a Anuar
# El 2026-08-04 Anuar dijo: "no sé cómo pedirle a AURORA sin que lance algo
# diferente... tú sabes cómo pienso y me expreso, pero no has podido integrar
# eso en aurora".
#
# Se midió con 23 frases reales suyas: 22 aciertan (95%), 0 van al motor
# equivocado. PERO 4 de esas 22 solo funcionan porque él YA se había peleado
# con ellas antes — el aprendizaje solo se activaba con el ciclo
# fallo -> reformulación. O sea: cada frase nueva le costaba un fracaso.
#
# Ahora, cuando ningún candado agarra el mensaje pero el enrutador con IA sí lo
# resuelve, la frase se registra EN EL MOMENTO. Sin reformular, sin pelearse.
# ===========================================================================
class TestAprendeALaPrimeraSinFallarAntes:

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_apr24", RAIZ / "CEREBRO" / "aprende_del_usuario.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_apr24"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_aprende_sin_fallo_previo(self):
        """registrar_exito EXIGE un fallo antes. Esto no."""
        import time
        a = self._mod()
        antes = len(a.listar())
        frase = "prueba regresion aprender a la primera xyz"
        try:
            r = a.aprender_a_la_primera(frase, "EDITOR/vectorizador:vectorizar", time.time())
            assert r is not None, "No aprendió sin fallo previo — vuelve a costarle un fracaso"
            assert r.get("a_la_primera") is True, "Falta la marca de que se aprendió sola"
            assert len(a.listar()) == antes + 1
            hallado = a.buscar(frase)
            assert hallado, "La registró pero no la vuelve a encontrar"
        finally:
            a.olvidar(frase)
            assert len(a.listar()) == antes, "Dejó basura en el perfil de Anuar"

    def test_no_aprende_basura(self):
        """Sin herramienta real no se aprende nada."""
        import time
        a = self._mod()
        antes = len(a.listar())
        assert a.aprender_a_la_primera("hola", "", time.time()) is None
        assert a.aprender_a_la_primera("", "X/y:z", time.time()) is None
        assert len(a.listar()) == antes

    def test_esta_cableado_al_enrutador(self):
        """De nada sirve la función si el pipeline no la llama."""
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert "aprender_a_la_primera" in fuente, (
            "El pipeline no aprende solo: cada frase nueva vuelve a costar un fallo")
        assert "_clave_usada" in fuente, (
            "El enrutador no dice qué herramienta usó, así que no hay qué aprender")

    def test_la_marca_interna_no_sale_al_usuario(self):
        """_clave_usada es de uso interno; si se filtra, Anuar ve basura técnica."""
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert 'real.pop("_clave_usada"' in fuente, (
            "La marca debe quitarse con pop antes de responder, no quedarse en el dict")


# ===========================================================================
# BUG 25 — El conocimiento cargado era inalcanzable hablando normal
# Al verificar la carga de 40 conocimientos reales (2026-08-04) se descubrió que
# entraban bien pero NO se alcanzaban con las preguntas que Anuar de verdad hace:
#
#   "que recuerdas de laser"      -> OK, 1.8 s
#   "a cuanto corto mdf de 2.7"   -> se iba al enrutador y ofrecia reajustar_grosor
#   "como va la lente del cañon"  -> motor_analisis INVENTÓ que la lente "fue
#                                    reemplazada el 2026-06-10" y que "no hay
#                                    registros de problemas". Ninguno de los dos
#                                    datos existe en ningún lado.
#
# Dos causas:
#   1. _buscar_semantico miraba SOLO la columna 'tema'. La receta del MDF vive
#      bajo el tema "laser", y la palabra "mdf" solo aparece en el texto, así que
#      no calzaba nunca — y se caía al respaldo de episodios, que devolvía un
#      precio viejo del MDF en vez de los parámetros de corte.
#   2. El candado de memoria solo reconocía "qué recuerdas de", que es justo la
#      forma que nadie usa.
# ===========================================================================
class TestElConocimientoSeAlcanzaHablandoNormal:

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc25", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc25"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _candado(self, mod, frase):
        for _n, trig, _m, motor in mod._CANDADOS:
            try:
                if trig(frase):
                    return motor
            except TypeError:
                pass
        return ""

    @pytest.mark.parametrize("frase", [
        "a cuanto corto mdf de 2.7",
        "que galga uso para el mdf",
        "a que potencia grabo",
        "como va la lente del cañon",
        "como esta el tubo",
    ])
    def test_preguntas_reales_llegan_a_la_memoria(self, frase):
        """Si no llegan aquí, caen en motor_analisis y ahí es donde inventa."""
        mod = self._mod()
        assert self._candado(mod, frase) == "memoria", (
            f"'{frase}' no alcanza el conocimiento cargado: vuelve a inventar")

    @pytest.mark.parametrize("frase,esperado", [
        ("como va la contabilidad", "negocio_real"),
        ("como vamos de ventas", "negocio_real"),
        ("cuanto cayo hoy", "negocio_real"),
        ("cotizame 20 termos", "cotizador"),
    ])
    def test_no_secuestra_las_del_negocio(self, frase, esperado):
        """'Cómo va X' del NEGOCIO debe seguir yendo a los datos reales."""
        mod = self._mod()
        assert self._candado(mod, frase) == esperado, f"Se rompió: '{frase}'"

    def test_la_busqueda_mira_el_contenido_no_solo_el_tema(self):
        fuente = (RAIZ / "MEMORIA" / "sistema_memoria.py").read_text(encoding="utf-8")
        i = fuente.index("def _buscar_semantico")
        bloque = fuente[i:i + 2200]
        assert "conocimiento LIKE" in bloque, (
            "Buscando solo por tema, 'mdf' nunca encuentra la receta que vive "
            "bajo el tema 'laser' — el conocimiento cargado queda inalcanzable")
        assert "patron LIKE" in bloque, "Falta buscar también en el patrón"


# ===========================================================================
# BUG 26 — Seis búsquedas seguidas sin un solo enlace útil
# Caso real 2026-08-04. Anuar pidió SEIS veces, reformulando cada vez, el precio
# del papel adhesivo en MercadoLibre. Las seis fallaron por tres causas juntas:
#
#   1. Se mandaba el mensaje COMPLETO al buscador. Literalmente se buscaba
#      "aurora busca en mercado libre ... copea el enllace aqui mismo".
#   2. No se respetaba el sitio pedido: decía "en mercado libre" y buscaba en
#      todo internet, devolviendo mercadolibre.com.ar entre otros.
#   3. No se filtraba nada. Devolvió fanx.art —un sitio de contenido para
#      adultos— en la casa donde su esposa y su hija usan AURORA.
#
# Y no se entregaban las URLs, que era LO que se pedía: el buscador sí las trae,
# se perdían al pasar por contexto_para_llm.
#
# Nota aparte, anotada para después: el aprendizaje NO ayudó en las 6 veces
# porque solo se activa cuando AURORA no ejecuta nada. Aquí sí ejecutaba (hacía
# la búsqueda), solo que devolvía basura. No distingue "hizo algo" de "sirvió".
# ===========================================================================
class TestBusquedaWebLimpiaYAcotada:

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc26", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc26"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_quita_las_instrucciones_de_la_consulta(self):
        """Buscar 'copea el enlace aqui mismo' es lo que traía la basura."""
        mod = self._mod()
        frase = ("aurora busca en mercado libre 100 hojas de papel adesivo para "
                 "imprecion laser al mejor precio y copea el enllace aqui mismo")
        limpia, dominio = mod.Consciencia._limpiar_consulta(frase)
        for basura in ("aurora", "copea", "enllace", "aqui mismo", "busca en"):
            assert basura not in limpia, f"Quedó '{basura}' en la consulta: {limpia}"
        assert "papel" in limpia and "laser" in limpia, (
            f"Se perdió lo que de verdad se busca: {limpia}")

    @pytest.mark.parametrize("frase,dominio", [
        ("busca en mercado libre papel adhesivo", "mercadolibre.com.mx"),
        ("busca en amazon vinil textil", "amazon.com.mx"),
        ("busca en lideart papel forever", "lideart.com.mx"),
    ])
    def test_respeta_el_sitio_que_se_pidio(self, frase, dominio):
        """Decir 'en mercado libre' y buscar en todo internet es no escuchar."""
        mod = self._mod()
        _limpia, dom = mod.Consciencia._limpiar_consulta(frase)
        assert dom == dominio, f"No acotó a {dominio}, dio '{dom}'"

    def test_busqueda_general_no_inventa_sitio(self):
        mod = self._mod()
        _l, dom = mod.Consciencia._limpiar_consulta("busca en internet precios de vinil")
        assert dom == "", "Acotó a un sitio que nadie pidió"

    def test_bloquea_dominios_para_adultos(self):
        """Devolvió fanx.art en la casa donde su hija usa AURORA."""
        mod = self._mod()
        bloq = mod.Consciencia._DOMINIOS_BLOQUEADOS
        for d in ("fanx.art", "undress", "nudify", "porn"):
            assert d in bloq, f"'{d}' no está bloqueado"

    def test_entrega_las_urls(self):
        """Se pedía el ENLACE. El buscador lo trae; se perdía en el camino.

        Se ancla en la función EXACTA (con el paréntesis) y se lee hasta el
        siguiente 'async def', no una ventana de N caracteres: la primera
        versión de esta prueba agarraba _buscar_web_candado, que va antes, y
        fallaba por eso — no porque el código estuviera mal.
        """
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        i = fuente.index("async def _buscar_web(self")
        resto = fuente[i + 10:]
        fin = resto.find("\n    async def ")
        bloque = resto[:fin] if fin > 0 else resto
        assert "url" in bloque, (
            "No arma la respuesta con las URLs: vuelve a contestar sin enlaces")
        assert "_limpiar_consulta" in bloque, (
            "No limpia la consulta: vuelve a buscar 'copea el enlace aqui mismo'")
        assert "_DOMINIOS_BLOQUEADOS" in bloque, (
            "No filtra los dominios de adultos que devolvió el 2026-08-04")


# ===========================================================================
# MEJORA 27 — Directorio de proveedores y captura de clientes por chat
# El barrido del 2026-08-04 encontró que ORACLE/oracle_core:crear_lead existía
# y NO tenía ninguna puerta desde el chat: un cliente que llamaba se anotaba en
# un papel o se perdía. De las 537 herramientas, esa es de las que más dinero
# mueve y era inalcanzable.
#
# Y ese mismo día Anuar no supo a quién cotizarle el papel adhesivo: no había
# directorio de proveedores en ningún lado, así que terminó pidiéndole a AURORA
# que buscara en MercadoLibre.
# ===========================================================================
class TestProveedoresYCapturaDeClientes:

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc27", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc27"] = mod
        spec.loader.exec_module(mod)
        return mod

    def _candado(self, mod, frase):
        for _n, trig, _m, motor in mod._CANDADOS:
            try:
                if trig(frase):
                    return motor
            except TypeError:
                pass
        return ""

    @pytest.mark.parametrize("frase", [
        "apunta a Juan Perez 3312345678 interesado en faros",
        "anota este cliente Maria 3339876543",
        "nuevo cliente Roberto quiere lupas",
        "registra un lead",
    ])
    def test_capturar_cliente_llega_a_oracle(self, frase):
        """Si no llega aquí, el cliente que llama se pierde."""
        mod = self._mod()
        assert self._candado(mod, frase) == "oracle_leads", (
            f"'{frase}' no da de alta al cliente")

    @pytest.mark.parametrize("frase", [
        "quien me vende vinil textil",
        "proveedor de mdf",
        "que proveedores tengo",
    ])
    def test_proveedor_antes_que_internet(self, frase):
        """Si el dato está en SU directorio, no hay que ir a internet."""
        mod = self._mod()
        assert self._candado(mod, frase) == "proveedores", (
            f"'{frase}' se va a buscar afuera teniendo el dato en casa")

    @pytest.mark.parametrize("frase,esperado", [
        ("busca en mercado libre papel adhesivo", "web_search"),
        ("ficha de aozoom x5", "vendedor"),
        ("cotizame 20 termos", "cotizador"),
        ("como va la contabilidad", "negocio_real"),
    ])
    def test_no_rompe_lo_que_ya_servia(self, frase, esperado):
        mod = self._mod()
        assert self._candado(mod, frase) == esperado, f"Se rompió: '{frase}'"

    def test_no_guarda_un_lead_sin_nombre(self):
        """Un cliente sin nombre no sirve para llamarle después."""
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        i = fuente.index("async def _alta_lead_real")
        bloque = fuente[i:i + 4000]
        assert "if not nombre" in bloque, (
            "Guarda leads vacíos, que es peor que no guardarlos")

    def test_el_directorio_no_inventa_proveedores(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_prov27", RAIZ / "TALLER" / "proveedores.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_prov27"] = mod
        spec.loader.exec_module(mod)
        r = mod.buscar("algo que no vende nadie xyz")
        assert r["status"] == "NO_LO_TENGO", "Inventó un proveedor"
        assert "internet" in r["detalle"].lower(), "No ofrece la salida real"

    def test_los_scripts_no_secuestran_la_salida(self):
        """Reemplazar sys.stdout al importar le rompe la salida a AURORA.
        Encontrado el 2026-08-05 al conectar proveedores al chat."""
        for ruta in ("TALLER/proveedores.py", "TALLER/indexar_dxf.py",
                     "SISTEMA/indexar_programas.py"):
            fuente = (RAIZ / ruta).read_text(encoding="utf-8")
            assert "def _consola_utf8" in fuente, (
                f"{ruta} toca sys.stdout al importarse")


# ===========================================================================
# BUG 28 — "qué recuerdas de cotizar" devolvió una cotización de faros
# Encontrado el 2026-08-05 verificando el conocimiento cargado. El candado del
# cotizador vio la palabra "cotizar" dentro de la pregunta y se lanzó, aunque
# lo que se pedía era consultar la MEMORIA.
#
# Y no era solo el cotizador: "qué recuerdas de video", "de proveedores", "de
# corel" tenían el mismo problema. Por eso el arreglo NO va dentro de cada
# candado — va como guard global en el pipeline: si se pregunta qué recuerda,
# solo la memoria contesta. Un parche por candado habría dejado abiertos los
# que nadie probó.
# ===========================================================================
class TestPreguntarQueRecuerdaNoDisparaLaAccion:

    def _mod(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("_cc28", RAIZ / "CEREBRO" / "consciencia.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cc28"] = mod
        spec.loader.exec_module(mod)
        return mod

    @pytest.mark.parametrize("frase", [
        "que recuerdas de cotizar",
        "que recuerdas de proveedores",
        "que recuerdas de video",
        "que sabes de corel",
        "que has aprendido de mi",
    ])
    def test_se_reconoce_como_pregunta_a_la_memoria(self, frase):
        mod = self._mod()
        assert mod._es_pregunta_de_memoria(mod._norm_txt(frase)), (
            f"'{frase}' no se reconoce como pregunta a la memoria: el nombre "
            "del tema va a secuestrar el mensaje")

    @pytest.mark.parametrize("frase", [
        "cotizame 20 termos",
        "quien me vende vinil",
        "voltea los videos a vertical",
        "como va la contabilidad",
    ])
    def test_pedir_la_accion_sigue_funcionando(self, frase):
        """El guard no debe apagar los candados cuando SÍ se pide la acción."""
        mod = self._mod()
        assert not mod._es_pregunta_de_memoria(mod._norm_txt(frase)), (
            f"'{frase}' se marcó como pregunta de memoria y no lo es")

    def test_el_guard_esta_en_el_pipeline_no_en_cada_candado(self):
        """Un parche por candado deja abiertos los que nadie probó."""
        fuente = (RAIZ / "CEREBRO" / "consciencia.py").read_text(encoding="utf-8")
        assert "_solo_memoria" in fuente, "Falta el guard global"
        assert "if _solo_memoria and _nombre_candado not in" in fuente, (
            "El guard no está aplicado en el bucle de candados")
