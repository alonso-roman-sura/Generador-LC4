"""
verificar_version.py - Comprueba que archivo hay en esta carpeta
================================================================
No abre el navegador ni genera nada. Solo inspecciona los archivos
y dice si estan actualizados o si quedo una version anterior.

USO
    python verificar_version.py
"""

from pathlib import Path
import argparse
import sys

AQUI = Path(__file__).resolve().parent

# Cada entrada: (etiqueta, texto que DEBE estar, texto que NO debe estar)
COMPROBACIONES = {
    "LC4_Generador.html": [
        ("contador de etiquetas corregido",
         "const reTag =",
         "const abre  = (xml.match(new RegExp"),
        ("selector 'Nombrar firmantes como'",
         'id="formatoFirmante"',
         None),
        ("firmanteTexto respeta el selector",
         "document.getElementById('formatoFirmante')?.value",
         None),
        ("enumeracion con comas",
         "function enumerar",
         None),
        ("consola de diagnostico LC4",
         "window.LC4",
         None),
        ("parser unico preview/documento",
         "function parseBloque",
         None),
    ],
    "probar_lc4.py": [
        ("comprobacion previa del archivo",
         "def revisar_archivo",
         None),
        ("registro de consola sin arrastre",
         "def vaciar_registro",
         None),
        ("mensajes de JavaScript legibles",
         "def errores_js",
         None),
    ],
    "build.bat": [
        ("script de compilacion",
         "#@PY_START",
         None),
    ],
    "template.html": [
        ("contador de etiquetas corregido",
         "const reTag =",
         "const abre  = (xml.match(new RegExp"),
        ("selector 'Nombrar firmantes como'",
         'id="formatoFirmante"',
         None),
        ("firmanteTexto respeta el selector",
         "document.getElementById('formatoFirmante')?.value",
         None),
    ],
}


def arreglar_saltos(ruta: Path) -> int:
    """Convierte un archivo a saltos de linea de Windows (CRLF).

    Devuelve cuantas lineas estaban en formato Unix. Cero significa que
    ya estaba bien y no se toco el archivo.
    """
    crudo = ruta.read_bytes()
    lf_solo = crudo.count(b"\n") - crudo.count(b"\r\n")
    if lf_solo == 0:
        return 0
    texto = crudo.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    ruta.write_bytes(texto.replace(b"\n", b"\r\n"))
    return lf_solo


def main():
    ap = argparse.ArgumentParser(
        description="Comprueba que los archivos de esta carpeta esten actualizados")
    ap.add_argument("--arreglar", action="store_true",
                    help="corrige los saltos de linea de los .bat en el sitio")
    args = ap.parse_args()

    if args.arreglar:
        print("=" * 64)
        print("  CORRECCION DE SALTOS DE LINEA EN ARCHIVOS .BAT")
        print("=" * 64)
        encontrados = sorted(AQUI.glob("*.bat"))
        if not encontrados:
            print("  No hay archivos .bat en esta carpeta.")
        for bat in encontrados:
            n = arreglar_saltos(bat)
            if n:
                print(f"  {bat.name:24} corregido ({n} lineas pasaron a CRLF)")
            else:
                print(f"  {bat.name:24} ya estaba correcto")
        print("=" * 64 + "\n")

    print("=" * 64)
    print("  VERIFICACION DE VERSIONES")
    print("=" * 64)
    print(f"  Carpeta: {AQUI}\n")

    desactualizados = []

    for archivo, pruebas in COMPROBACIONES.items():
        ruta = AQUI / archivo
        if not ruta.exists():
            print(f"  {archivo}")
            print(f"     no esta en esta carpeta\n")
            continue

        try:
            texto = ruta.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  {archivo}\n     no se pudo leer: {e}\n")
            continue

        kb = ruta.stat().st_size // 1024
        fallos = []
        for etiqueta, debe, no_debe in pruebas:
            if debe not in texto:
                fallos.append(f"falta: {etiqueta}")
            elif no_debe and no_debe in texto:
                fallos.append(f"conserva codigo antiguo: {etiqueta}")

        # Los .bat necesitan saltos de linea de Windows (CRLF). Con saltos
        # de Unix, CMD parte los comandos a la mitad y falla al ejecutarse.
        if archivo.lower().endswith(".bat"):
            crudo = ruta.read_bytes()
            crlf = crudo.count(b"\r\n")
            lf_solo = crudo.count(b"\n") - crlf
            if lf_solo > 0:
                fallos.append(
                    f"saltos de linea de Unix ({lf_solo} lineas) - CMD no podra ejecutarlo")

        estado = "ACTUALIZADO" if not fallos else "DESACTUALIZADO"
        print(f"  {archivo}  ({kb} KB)  ->  {estado}")
        for f in fallos:
            print(f"     - {f}")
        if fallos:
            desactualizados.append(archivo)
        print()

    # La carpeta assets solo hace falta para recompilar, no para usar la
    # herramienta. Se avisa como nota, no como fallo.
    assets = AQUI / "assets"
    if not assets.is_dir():
        print("  Nota: no hay carpeta 'assets' en esta ubicacion.")
        print("        Solo se necesita para recompilar con build.bat.")
        print("        Para usar el generador basta LC4_Generador.html.\n")
    else:
        faltantes = [n for n in ("template.docx", "banner.jpg", "jszip.min.js",
                                 "FileSaver.min.js") if not (assets / n).exists()]
        n_fuentes = len(list((assets / "fonts").glob("*.otf"))) if (assets / "fonts").is_dir() else 0
        if faltantes or n_fuentes < 16:
            print("  Nota sobre la carpeta 'assets':")
            for n in faltantes:
                print(f"        falta {n}")
            if n_fuentes < 16:
                print(f"        hay {n_fuentes} fuentes .otf, se esperan 16")
            print()

    print("=" * 64)
    if desactualizados:
        solo_saltos = all(a.lower().endswith(".bat") for a in desactualizados)
        print("  Hay que revisar:")
        for a in desactualizados:
            print(f"     - {a}")
        if solo_saltos:
            print("\n  El unico problema son los saltos de linea. Se corrige con:")
            print("\n      python verificar_version.py --arreglar\n")
            print("  No hace falta descargar nada de nuevo.")
        else:
            print("\n  Descargar de nuevo esos archivos y sobrescribir los de esta")
            print("  carpeta. Verificar que la descarga no haya quedado con nombre")
            print("  del tipo 'LC4_Generador (1).html' en la carpeta de descargas.")
    else:
        print("  Todos los archivos estan actualizados.")
        print("  Ya se puede ejecutar:  python probar_lc4.py")
    print("=" * 64)

    sys.exit(1 if desactualizados else 0)


if __name__ == "__main__":
    main()