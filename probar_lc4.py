"""
probar_lc4.py - Banco de pruebas del Generador LC4
===================================================
Abre LC4_Generador.html en Chrome, recorre distintas combinaciones de
representantes, modalidades y facultades, descarga los documentos y
verifica que cada .docx generado sea valido.

A diferencia de una revision manual, ejecuta el navegador de verdad:
comprueba el flujo completo, incluida la descarga del archivo.

REQUISITOS
    pip install selenium
    Chrome instalado (Selenium descarga el driver automaticamente)

USO
    python probar_lc4.py                      todos los casos, sin ventana
    python probar_lc4.py --visible            muestra el navegador
    python probar_lc4.py --caso 3             solo el caso numero 3
    python probar_lc4.py --html "ruta.html"   indica otro archivo
    python probar_lc4.py --conservar          no borra los .docx generados

SALIDA
    Un resumen por caso y, si algo falla, el detalle del problema.
    Los documentos quedan en la carpeta  _pruebas_lc4  junto al script.
"""

import argparse
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from html import unescape

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select
except ImportError:
    print("Falta Selenium. Instalar con:\n\n    pip install selenium\n")
    sys.exit(1)


AQUI = Path(__file__).resolve().parent
DESCARGAS = AQUI / "_pruebas_lc4"

MARCADORES = ['__LC4_FECHA__', '__LC4_CUC__', '__LC4_EMPRESA__',
              '__LC4_REPRESENTANTES__', '__LC4_FACULTADES__', '__LC4_OBSERVACIONES__']


# ══════════════════════════════════════════════════════════════════════
#  CASOS DE PRUEBA
#  Cada caso describe que se llena en el formulario. Para agregar uno
#  nuevo, basta con copiar un diccionario y cambiar los valores.
# ══════════════════════════════════════════════════════════════════════

CASOS = [
    {
        "nombre": "Un apoderado, a sola firma",
        "empresa": "EMPRESA UNO S.A.C.",
        "cuc": "44760645",
        "observaciones": "",
        "formato": "cargo",
        "representantes": [
            {"nombre": "PEREZ PEPITO", "cargo": "APODERADO", "clase": "Clase A"},
        ],
        "bloques": [
            {"firmantes": [0], "modalidad": "sola", "facultades": [0, 1], "texto": ""},
        ],
    },
    {
        "nombre": "Dos apoderados a sola firma (enumeracion con y)",
        "empresa": "EMPRESA DOS S.A.C.",
        "cuc": "",
        "observaciones": "Sin restricciones adicionales.",
        "formato": "cargo",
        "representantes": [
            {"nombre": "PEREZ PEPITO", "cargo": "APODERADO", "clase": "Clase A"},
            {"nombre": "JUAN PEREZ", "cargo": "APODERADO", "clase": "Clase C"},
        ],
        "bloques": [
            {"firmantes": [0, 1], "modalidad": "sola", "facultades": [0, 1, 2], "texto": ""},
        ],
    },
    {
        "nombre": "Mancomunada entre gerente y tesorero",
        "empresa": "EMPRESA TRES S.A.",
        "cuc": "12345678",
        "observaciones": "Monto maximo US$ 750,000.00 por operacion.",
        "formato": "cargo",
        "representantes": [
            {"nombre": "GARCIA LOPEZ JUAN", "cargo": "GERENTE GENERAL", "clase": ""},
            {"nombre": "MENDOZA RIOS PEDRO", "cargo": "TESORERO", "clase": ""},
        ],
        "bloques": [
            {"firmantes": [0, 1], "modalidad": "mancomunada", "facultades": [0, 3], "texto": ""},
        ],
    },
    {
        "nombre": "Por grupos (1 con 2)",
        "empresa": "EMPRESA CUATRO S.A.C.",
        "cuc": "99887766",
        "observaciones": "",
        "formato": "cargo",
        "representantes": [
            {"nombre": "GARCIA LOPEZ JUAN", "cargo": "GERENTE GENERAL", "clase": ""},
            {"nombre": "MENDOZA RIOS PEDRO", "cargo": "TESORERO", "clase": ""},
            {"nombre": "FLORES VERA ANA", "cargo": "APODERADO", "clase": "Clase A"},
        ],
        "bloques": [
            {"firmantes": [0, 1, 2], "modalidad": "grupos", "grupos": ["1", "1", "2"],
             "facultades": [0, 1], "texto": ""},
        ],
    },
    {
        "nombre": "Dos bloques con condiciones distintas",
        "empresa": "EMPRESA CINCO S.A.",
        "cuc": "",
        "observaciones": "Linea uno\nLinea dos\nLinea tres",
        "formato": "cargo",
        "representantes": [
            {"nombre": "GARCIA LOPEZ JUAN", "cargo": "GERENTE GENERAL", "clase": ""},
            {"nombre": "MENDOZA RIOS PEDRO", "cargo": "TESORERO", "clase": ""},
            {"nombre": "FLORES VERA ANA", "cargo": "APODERADO", "clase": "Clase B"},
        ],
        "bloques": [
            {"firmantes": [0, 1], "modalidad": "mancomunada", "facultades": [0], "texto": ""},
            {"firmantes": [2], "modalidad": "sola", "facultades": [],
             "texto": "- Suscribir contratos de arrendamiento.\n- Representar a la sociedad ante entidades publicas."},
        ],
    },
    {
        "nombre": "Formato por nombre",
        "empresa": "EMPRESA SEIS S.A.C.",
        "cuc": "11223344",
        "observaciones": "",
        "formato": "nombre",
        "representantes": [
            {"nombre": "PEREZ PEPITO", "cargo": "APODERADO", "clase": "Clase A"},
            {"nombre": "RAMIREZ ANA", "cargo": "TESORERO", "clase": ""},
        ],
        "bloques": [
            {"firmantes": [0, 1], "modalidad": "mancomunada", "facultades": [1, 4], "texto": ""},
        ],
    },
    {
        "nombre": "Formato cargo y nombre",
        "empresa": "EMPRESA SIETE S.A.",
        "cuc": "",
        "observaciones": "",
        "formato": "ambos",
        "representantes": [
            {"nombre": "PEREZ PEPITO", "cargo": "APODERADO", "clase": "Clase A"},
        ],
        "bloques": [
            {"firmantes": [0], "modalidad": "sola", "facultades": [5, 6, 7], "texto": ""},
        ],
    },
    {
        "nombre": "Combinacion libre",
        "empresa": "EMPRESA OCHO S.A.C.",
        "cuc": "55667788",
        "observaciones": "Cualquier operacion que exceda el monto requiere junta.",
        "formato": "cargo",
        "representantes": [
            {"nombre": "ARNAIZ FIGALLO MARIA", "cargo": "APODERADO", "clase": "Clase A"},
            {"nombre": "CALLE QUIROS JUAN", "cargo": "GERENTE GENERAL", "clase": ""},
        ],
        "bloques": [
            {"firmantes": [0], "modalidad": "libre",
             "libre": "conjuntamente con el Gerente General o con otro apoderado clase A",
             "facultades": [0, 1, 2], "texto": ""},
        ],
    },
    {
        "nombre": "Caracteres especiales en todos los campos",
        "empresa": 'INVERSIONES $1 & CIA <S.A.C.> "X"',
        "cuc": "0",
        "observaciones": "Monto US$ 750,000 & <revision> $1",
        "formato": "cargo",
        "representantes": [
            {"nombre": "O'BRIEN & ASOCIADOS", "cargo": "APODERADO", "clase": 'Clase "A" & B'},
        ],
        "bloques": [
            {"firmantes": [0], "modalidad": "sola", "facultades": [],
             "texto": "- Operar cuentas <especiales> & afines\nParrafo con & y < sin guion"},
        ],
    },
    {
        "nombre": "Cargo personalizado y texto mixto",
        "empresa": "EMPRESA DIEZ S.A.",
        "cuc": "",
        "observaciones": "",
        "formato": "cargo",
        "representantes": [
            {"nombre": "TORRES SILVA LUIS", "cargo": "__custom__",
             "cargo_texto": "DIRECTOR FINANCIERO", "clase": ""},
        ],
        "bloques": [
            {"firmantes": [0], "modalidad": "sola", "facultades": [0],
             "texto": "Ademas de lo anterior:\n- Aprobar presupuestos anuales.\n- Autorizar gastos operativos."},
        ],
    },
    {
        "nombre": "Modo texto manual",
        "empresa": "EMPRESA ONCE S.A.C.",
        "cuc": "77889900",
        "observaciones": "",
        "modo_manual": "En forma mancomunada con otro apoderado autorizado en todas las ciudades "
                       "del pais y/o el extranjero podra:\n"
                       "- Realizar toda clase de operaciones bancarias y financieras.\n"
                       "- Suscribir contratos, asi como cualquier tipo de contrato bancario.",
        "representantes": [
            {"nombre": "MARTINEZ NUNEZ CESAR", "cargo": "APODERADO", "clase": ""},
            {"nombre": "PESCHIERA FERNANDEZ MARCO", "cargo": "APODERADO", "clase": ""},
        ],
        "bloques": [],
    },
]


# ══════════════════════════════════════════════════════════════════════
#  NAVEGADOR
# ══════════════════════════════════════════════════════════════════════

def abrir_navegador(visible: bool) -> webdriver.Chrome:
    DESCARGAS.mkdir(exist_ok=True)
    op = Options()
    if not visible:
        op.add_argument("--headless=new")
    op.add_argument("--window-size=1280,1400")
    op.add_argument("--disable-gpu")
    op.add_argument("--log-level=3")
    op.add_experimental_option("excludeSwitches", ["enable-logging"])
    op.add_experimental_option("prefs", {
        "download.default_directory": str(DESCARGAS),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    drv = webdriver.Chrome(options=op)
    # En modo headless hay versiones de Chrome que ignoran las preferencias
    # de descarga; esto lo fuerza por el protocolo de depuracion.
    try:
        drv.execute_cdp_cmd("Page.setDownloadBehavior",
                            {"behavior": "allow", "downloadPath": str(DESCARGAS)})
    except Exception:
        pass
    return drv


def vaciar_registro(drv):
    """Descarta los mensajes de consola acumulados.

    Es necesario porque el registro de Chrome no se limpia solo: los errores
    de un caso apareceran al leerlo en el siguiente y se atribuirian al caso
    equivocado.
    """
    try:
        drv.get_log("browser")
    except Exception:
        pass


def errores_js(drv):
    """Devuelve los errores de JavaScript ocurridos desde la ultima lectura."""
    fuera = []
    try:
        for entrada in drv.get_log("browser"):
            if entrada["level"] != "SEVERE":
                continue
            msg = entrada["message"]
            if "favicon" in msg:
                continue
            # El mensaje llega como "<url> <linea>:<col> <texto>". Nos quedamos
            # con el texto, que es lo unico util para diagnosticar.
            limpio = re.sub(r"^\S+\s+\d+:\d+\s+", "", msg).strip()
            fuera.append(limpio or msg)
    except Exception:
        pass
    return fuera


def js_click(drv, elemento):
    """Clic por JavaScript: funciona aunque el elemento este fuera de vista."""
    drv.execute_script("arguments[0].click();", elemento)


def escribir(drv, elem_id, texto):
    """Escribe en un campo disparando los eventos que la pagina espera."""
    drv.execute_script("""
        const el = document.getElementById(arguments[0]);
        if (!el) throw new Error('No existe el campo ' + arguments[0]);
        el.value = arguments[1];
        el.dispatchEvent(new Event('input',  {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    """, elem_id, texto)


def ids_representantes(drv):
    return drv.execute_script(
        "return [...document.querySelectorAll('.rep-block')].map(b => b.id.replace('rep-',''));")


def ids_bloques(drv):
    return drv.execute_script(
        "return [...document.querySelectorAll('.bloque-act')].map(b => b.id.replace('bloque-',''));")


# ══════════════════════════════════════════════════════════════════════
#  LLENADO DEL FORMULARIO
# ══════════════════════════════════════════════════════════════════════

def llenar(drv, caso):
    escribir(drv, "fecha", "2026-08-04")
    escribir(drv, "cuc", caso.get("cuc", ""))
    escribir(drv, "empresa", caso["empresa"])
    escribir(drv, "observaciones", caso.get("observaciones", ""))

    # ── Representantes ──────────────────────────────────────────────
    reps = caso["representantes"]
    while len(ids_representantes(drv)) < len(reps):
        js_click(drv, drv.find_element(By.CSS_SELECTOR, ".btn-add-rep"))
    rids = ids_representantes(drv)

    for i, r in enumerate(reps):
        rid = rids[i]
        escribir(drv, f"nombre-{rid}", r["nombre"])
        sel = Select(drv.find_element(By.ID, f"cargo-select-{rid}"))
        sel.select_by_value(r["cargo"])
        drv.execute_script(f"onCargoChange({rid});")
        if r["cargo"] == "__custom__":
            escribir(drv, f"cargo-custom-{rid}", r.get("cargo_texto", "CARGO"))
        if r.get("clase"):
            escribir(drv, f"clase-{rid}", r["clase"])

    drv.execute_script("syncBloquesFirmantes();")

    # ── Modo texto manual ───────────────────────────────────────────
    if caso.get("modo_manual"):
        drv.execute_script("setFacMode('manual');")
        escribir(drv, "facManual", caso["modo_manual"])
        return

    drv.execute_script("setFacMode('plantilla');")
    if caso.get("formato"):
        Select(drv.find_element(By.ID, "formatoFirmante")).select_by_value(caso["formato"])
        drv.execute_script("updatePreview();")

    # ── Bloques de actuacion ────────────────────────────────────────
    bloques = caso["bloques"]
    while len(ids_bloques(drv)) < len(bloques):
        js_click(drv, drv.find_elements(By.CSS_SELECTOR, ".btn-add-rep")[-1])
    bids = ids_bloques(drv)

    MODO_HTML = {"sola": "sola", "mancomunada": "manco", "grupos": "grupos", "libre": "libre"}

    for i, bl in enumerate(bloques):
        bid = bids[i]
        for idx in bl["firmantes"]:
            js_click(drv, drv.find_element(By.ID, f"fchk-{bid}-{rids[idx]}"))
        js_click(drv, drv.find_element(By.ID, f"bmodo-{MODO_HTML[bl['modalidad']]}-{bid}"))

        if bl["modalidad"] == "grupos":
            for k, idx in enumerate(bl["firmantes"]):
                g = bl.get("grupos", ["1"] * len(bl["firmantes"]))[k]
                radio = drv.find_elements(
                    By.CSS_SELECTOR, f'input[name="grupo-{bid}-{rids[idx]}"][value="{g}"]')
                if radio:
                    js_click(drv, radio[0])

        if bl["modalidad"] == "libre" and bl.get("libre"):
            escribir(drv, f"bcombo-text-{bid}", bl["libre"])
            drv.execute_script(f"onBloqueChange({bid});")

        for f in bl.get("facultades", []):
            js_click(drv, drv.find_element(By.ID, f"bchk-{bid}-{f}"))

        if bl.get("texto"):
            actual = drv.execute_script(
                f"return document.getElementById('bfac-text-{bid}').value;")
            nuevo = (actual + "\n" + bl["texto"]) if actual else bl["texto"]
            escribir(drv, f"bfac-text-{bid}", nuevo)
            drv.execute_script(f"onFacTextInput({bid}, document.getElementById('bfac-text-{bid}'));")


# ══════════════════════════════════════════════════════════════════════
#  GENERACION Y ESPERA DE LA DESCARGA
# ══════════════════════════════════════════════════════════════════════

def generar_y_esperar(drv, timeout=25):
    previos = {p.name for p in DESCARGAS.glob("*.docx")}
    js_click(drv, drv.find_element(By.ID, "btnGen"))

    fin = time.time() + timeout
    while time.time() < fin:
        time.sleep(0.4)
        nuevos = {p.name for p in DESCARGAS.glob("*.docx")} - previos
        parciales = list(DESCARGAS.glob("*.crdownload"))
        if nuevos and not parciales:
            return DESCARGAS / nuevos.pop(), None
        toast = drv.execute_script(
            "const t=document.getElementById('toast');"
            "return t && t.className.includes('err') ? t.textContent.trim() : null;")
        if toast:
            return None, toast
    return None, "tiempo agotado esperando la descarga"


# ══════════════════════════════════════════════════════════════════════
#  VALIDACION DEL DOCX
# ══════════════════════════════════════════════════════════════════════

def validar_docx(ruta: Path):
    """Devuelve la lista de problemas encontrados. Vacia significa correcto."""
    problemas = []
    try:
        with zipfile.ZipFile(ruta) as z:
            nombres = z.namelist()
            if "word/document.xml" not in nombres:
                return ["el archivo no contiene word/document.xml"]
            xml = z.read("word/document.xml").decode("utf-8")
            num = z.read("word/numbering.xml").decode("utf-8") if "word/numbering.xml" in nombres else ""
    except zipfile.BadZipFile:
        return ["el archivo no es un .docx valido (zip corrupto)"]

    # 1. XML bien formado - es lo que hace que Word acepte o rechace el archivo
    try:
        ET.fromstring(xml)
    except ET.ParseError as e:
        problemas.append(f"XML mal formado: {e}")
    if num:
        try:
            ET.fromstring(num)
        except ET.ParseError as e:
            problemas.append(f"numbering.xml mal formado: {e}")

    # 2. Ninguna celda de tabla sin parrafo
    for celda in re.finditer(r"<w:tc>.*?</w:tc>", xml, re.DOTALL):
        if "<w:p" not in celda.group():
            problemas.append("hay una celda de tabla sin parrafo")
            break

    # 3. Marcadores reemplazados
    for m in MARCADORES:
        if m in xml:
            problemas.append(f"quedo el marcador {m}")

    # 4. Toda lista usada debe estar definida
    for numid in set(re.findall(r'w:numId w:val="(\d+)"', xml)):
        if f'<w:num w:numId="{numid}"' not in num:
            problemas.append(f"la lista numId={numid} no esta definida")

    # 5. Restos de variables sin inicializar
    if re.search(r'w:val="(null|undefined|NaN)"', xml):
        problemas.append("hay un atributo con valor null o undefined")

    return problemas


def texto_del_docx(ruta: Path, marca: str):
    """Extrae el texto de la celda que sigue a una etiqueta dada.

    Deshace las entidades XML (&amp;, &quot;, ...) para mostrar el texto
    tal como se vera en Word y no como esta guardado en el archivo.
    """
    with zipfile.ZipFile(ruta) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    celdas = re.findall(r"<w:tc>.*?</w:tc>", xml, re.DOTALL)
    for i, c in enumerate(celdas):
        texto = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", c))
        if marca.lower() in texto.lower() and i + 1 < len(celdas):
            crudo = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", celdas[i + 1]))
            return unescape(crudo)
    return ""


# ══════════════════════════════════════════════════════════════════════
#  COMPROBACION PREVIA DEL ARCHIVO
# ══════════════════════════════════════════════════════════════════════

def revisar_archivo(drv):
    """Verifica que el HTML bajo prueba este completo y sea una version sana.

    Se ejecuta antes de los casos. Si el archivo trae un fallo conocido,
    conviene avisarlo de una vez en lugar de que todos los casos fallen con
    mensajes que apuntan al sintoma y no a la causa.
    """
    problemas = []

    faltan = drv.execute_script("""
        const req = ['X','setFacMode','parseBloque','buildBloqueIntro','buildFacXml',
                     'buildRepsXml','enumerar','firmanteTexto','replaceLiteral',
                     'replaceParagraph','registrarListaGuion','validarXml'];
        return req.filter(f => typeof window[f] !== 'function');
    """)
    if faltan:
        problemas.append("faltan funciones en el archivo: " + ", ".join(faltan))

    if not drv.execute_script("return !!document.getElementById('formatoFirmante');"):
        problemas.append("falta el selector 'Nombrar firmantes como'")

    # Prueba directa del validador: se le pasa un XML sano. Si lo rechaza,
    # el archivo tiene la version antigua del contador de etiquetas, que
    # daba falsos positivos y bloqueaba cualquier descarga.
    falsos = drv.execute_script("""
        const xml = '<w:tbl><w:tblPr><w:tblW w:w="9638" w:type="dxa"/></w:tblPr>'
          + '<w:tr><w:trPr><w:trHeight w:val="288"/></w:trPr>'
          + '<w:tc><w:tcPr><w:tcW w:w="100" w:type="dxa"/></w:tcPr>'
          + '<w:p><w:pPr><w:rPr><w:rFonts w:ascii="Sura Sans"/></w:rPr></w:pPr>'
          + '<w:r><w:rPr><w:rFonts w:ascii="Sura Sans"/></w:rPr><w:t>ok</w:t></w:r>'
          + '</w:p></w:tc></w:tr></w:tbl>';
        const num = '<w:numbering><w:num w:numId="17"><w:abstractNumId w:val="16"/></w:num></w:numbering>';
        try { return validarXml(xml, num).filter(p => !p.includes('marcador')); }
        catch (e) { return ['excepcion en validarXml: ' + e.message]; }
    """)
    if falsos:
        problemas.append(
            "el validador interno rechaza un XML correcto -> "
            + falsos[0]
            + "\n         Es el fallo del contador de etiquetas de las versiones antiguas."
            + "\n         Hay que reemplazar el LC4_Generador.html por la version corregida.")

    return problemas


# ══════════════════════════════════════════════════════════════════════
#  PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="Banco de pruebas del Generador LC4")
    ap.add_argument("--html", default=str(AQUI / "LC4_Generador.html"),
                    help="ruta del LC4_Generador.html a probar")
    ap.add_argument("--visible", action="store_true", help="muestra el navegador")
    ap.add_argument("--caso", type=int, help="ejecuta solo ese numero de caso")
    ap.add_argument("--conservar", action="store_true",
                    help="no borra los documentos generados al terminar")
    args = ap.parse_args()

    html = Path(args.html).resolve()
    if not html.exists():
        print(f"No se encontro el archivo:\n  {html}\n"
              f"Indicar la ruta con  --html \"C:\\ruta\\LC4_Generador.html\"")
        sys.exit(1)

    if DESCARGAS.exists():
        shutil.rmtree(DESCARGAS, ignore_errors=True)
    DESCARGAS.mkdir(exist_ok=True)

    casos = CASOS if args.caso is None else [CASOS[args.caso - 1]]

    print("=" * 66)
    print("  BANCO DE PRUEBAS - GENERADOR LC4")
    print("=" * 66)
    print(f"  Archivo : {html.name}")
    print(f"  Casos   : {len(casos)}")
    print(f"  Ventana : {'visible' if args.visible else 'oculta'}")
    print("=" * 66 + "\n")

    drv = abrir_navegador(args.visible)
    fallos = []

    try:
        # ── Comprobacion previa del archivo ──────────────────────────
        drv.get(html.as_uri())
        time.sleep(0.7)
        defectos = revisar_archivo(drv)
        if defectos:
            print("  EL ARCHIVO NO ESTA EN CONDICIONES DE SER PROBADO\n")
            for d in defectos:
                print(f"     - {d}")
            print("\n  No se ejecutan los casos: fallarian todos por la misma causa.")
            print("=" * 66)
            drv.quit()
            sys.exit(1)
        print("  Comprobacion previa del archivo: correcta\n")

        for i, caso in enumerate(casos, 1):
            n = args.caso or i
            print(f"[{n:2}] {caso['nombre']}")
            drv.get(html.as_uri())
            time.sleep(0.7)
            vaciar_registro(drv)   # descartar lo que quedo del caso anterior

            try:
                llenar(drv, caso)
            except Exception as e:
                print(f"     FALLO al llenar el formulario: {e}\n")
                fallos.append((caso["nombre"], f"llenado: {e}"))
                continue

            errs = errores_js(drv)
            if errs:
                print(f"     FALLO error de JavaScript al llenar: {errs[0][:180]}\n")
                fallos.append((caso["nombre"], f"js: {errs[0][:180]}"))
                continue

            archivo, error = generar_y_esperar(drv)
            if error:
                detalle = errores_js(drv)
                print(f"     FALLO no se genero el documento: {error}")
                if detalle:
                    print(f"            consola: {detalle[0][:180]}")
                print()
                fallos.append((caso["nombre"], error))
                continue

            problemas = validar_docx(archivo)
            if problemas:
                print(f"     FALLO documento invalido:")
                for p in dict.fromkeys(problemas):
                    print(f"            - {p}")
                fallos.append((caso["nombre"], "; ".join(problemas)))
                continue

            detalle = texto_del_docx(archivo, "DETALLE DE FIRMANTES")
            print(f"     ok   {archivo.name}  ({archivo.stat().st_size // 1024} KB)")
            if detalle:
                print(f"          {detalle[:110]}{'...' if len(detalle) > 110 else ''}")
            print()

    finally:
        drv.quit()

    print("=" * 66)
    if fallos:
        print(f"  {len(casos) - len(fallos)}/{len(casos)} correctos - {len(fallos)} FALLOS\n")
        for nombre, det in fallos:
            print(f"  - {nombre}\n      {det}")
    else:
        print(f"  {len(casos)}/{len(casos)} CORRECTOS")
        print("\n  Los documentos generados quedaron en:")
        print(f"    {DESCARGAS}")
        print("\n  Conviene abrir uno o dos en Word para revisar el formato:")
        print("  la validacion comprueba que el archivo sea correcto, pero no")
        print("  como se ve una vez abierto.")
    print("=" * 66)

    if not args.conservar and not fallos:
        respuesta = input("\nBorrar los documentos generados? (s/N): ").strip().lower()
        if respuesta == "s":
            shutil.rmtree(DESCARGAS, ignore_errors=True)
            print("Carpeta borrada.")

    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()