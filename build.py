import argparse, base64, sys, zipfile, re
from pathlib import Path

HERE      = Path(__file__).parent
ASSETS    = HERE / "assets"
FONTS_DIR = ASSETS / "fonts"
TMPL_HTML = HERE / "template.html"

FONTS = {
    "FONT_THIN":"SuraSans-Thin.otf","FONT_THIN_ITALIC":"SuraSans-ThinItalic.otf",
    "FONT_EXTRALIGHT":"SuraSans-ExtraLight.otf","FONT_EXTRALIGHT_ITALIC":"SuraSans-ExtraLightItalic.otf",
    "FONT_LIGHT":"SuraSans-Light.otf","FONT_LIGHT_ITALIC":"SuraSans-LightItalic.otf",
    "FONT_REGULAR":"SuraSans-Regular.otf","FONT_ITALIC":"SuraSans-Italic.otf",
    "FONT_SEMIBOLD":"SuraSans-SemiBold.otf","FONT_SEMIBOLD_ITALIC":"SuraSans-SemiBoldItalic.otf",
    "FONT_BOLD":"SuraSans-Bold.otf","FONT_BOLD_ITALIC":"SuraSans-BoldItalic.otf",
    "FONT_EXTRABOLD":"SuraSans-ExtraBold.otf","FONT_EXTRABOLD_ITALIC":"SuraSans-ExtraBoldItalic.otf",
    "FONT_BLACK":"SuraSans-Black.otf","FONT_BLACK_ITALIC":"SuraSans-BlackItalic.otf",
}

MARKERS = ['__LC4_FECHA__','__LC4_CUC__','__LC4_EMPRESA__',
           '__LC4_REPRESENTANTES__','__LC4_FACULTADES__','__LC4_OBSERVACIONES__']

def b64(p): return base64.b64encode(p.read_bytes()).decode("ascii")

def verify():
    with zipfile.ZipFile(ASSETS/"template.docx") as z:
        xml = z.read("word/document.xml").decode("utf-8")
    ok = True
    for m in MARKERS:
        count = xml.count(m)
        print(f"  {'OK' if count else 'FALTA'}  {m} ({count} ocurrencia/s)")
        if not count: ok = False
    print("\n" + ("Todos los marcadores encontrados." if ok else "Algunos marcadores no encontrados."))
    return ok

def build(out_path):
    html = TMPL_HTML.read_text(encoding="utf-8")
    print("Encodificando fuentes...")
    for marker, filename in FONTS.items():
        p = FONTS_DIR/filename
        html = html.replace(f"{{{{{marker}}}}}", b64(p) if p.exists() else "")
        if p.exists(): print(f"  OK  {filename}")
    print("Encodificando banner...")
    html = html.replace("{{BANNER_B64}}", b64(ASSETS/"banner.jpg"))
    print("Encodificando template.docx...")
    html = html.replace("{{TEMPLATE_B64}}", b64(ASSETS/"template.docx"))
    print("Inyectando librerias JS...")
    html = html.replace("{{JSZIP}}", (ASSETS/"jszip.min.js").read_text(encoding="utf-8"))
    html = html.replace("{{FILESAVER}}", (ASSETS/"FileSaver.min.js").read_text(encoding="utf-8"))
    rem = re.findall(r'\{\{[A-Z_]+\}\}', html)
    if rem: print(f"ADVERTENCIA -- Marcadores sin reemplazar: {rem}")
    out_path.write_text(html, encoding="utf-8")
    print(f"\nOK  {out_path}  ({out_path.stat().st_size//1024} KB)")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--out", type=Path, default=HERE/"LC4_Generador.html")
    args = p.parse_args()
    if args.verify:
        sys.exit(0 if verify() else 1)
    build(args.out)