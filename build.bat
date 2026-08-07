@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  build.bat  -  Ensamblador del Generador LC4
::  SURA Investments Peru . Cumplimiento Corporativo
:: ============================================================
::
::  Uso:
::    Doble clic            -> genera LC4_Generador.html
::    build.bat --verify    -> verifica marcadores en template.docx
::    build.bat --out ruta  -> especifica ruta de salida
::
::  Estructura de carpetas requerida (junto a este archivo):
::    assets\
::      template.docx   (con marcadores __LC4_*__)
::      banner.jpg
::      jszip.min.js
::      FileSaver.min.js
::      fonts\  (16 archivos SuraSans-*.otf)
::    template.html
:: ============================================================

:: IMPORTANTE: guardar la ruta del propio script ANTES de procesar los
:: argumentos. El comando SHIFT desplaza tambien %0, de modo que despues
:: de leer un argumento %~f0 ya no apunta a este archivo.
set "SELF=%~f0"

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "OUT=%SCRIPT_DIR%\LC4_Generador.html"
set "VERIFY=0"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--verify" ( set "VERIFY=1" & shift & goto parse_args )
if /i "%~1"=="--out"    ( set "OUT=%~2"  & shift & shift & goto parse_args )
shift & goto parse_args
:args_done

set "PY="
python --version >nul 2>&1  && set "PY=python"
if not defined PY python3 --version >nul 2>&1 && set "PY=python3"
if not defined PY (
    echo.
    echo  ERROR: Python no encontrado.
    echo  Instala Python 3 desde https://www.python.org/downloads/
    echo  y marca "Add Python to PATH" durante la instalacion.
    echo.
    pause & exit /b 1
)

set "TMP_PY=%TEMP%\lc4_build_%RANDOM%.py"

powershell -NoProfile -Command ^
    "$lines = Get-Content -Encoding UTF8 '%SELF%';" ^
    "$capture = $false; $out = [System.Collections.Generic.List[string]]::new();" ^
    "foreach ($line in $lines) {" ^
        "if ($line -eq '#@PY_START') { $capture = $true; continue };" ^
        "if ($line -eq '#@PY_END')   { break };" ^
        "if ($capture) { $out.Add($line) }" ^
    "};" ^
    "[IO.File]::WriteAllLines('%TMP_PY%', $out, [Text.UTF8Encoding]::new($false))"

if not exist "%TMP_PY%" (
    echo.
    echo  ERROR: No se pudo extraer el script Python.
    pause & exit /b 1
)

%PY% "%TMP_PY%" "%SCRIPT_DIR%" "%OUT%" "%VERIFY%"
set "EXIT_CODE=%errorlevel%"
del "%TMP_PY%" >nul 2>&1

if %EXIT_CODE% neq 0 (
    echo.
    echo  El proceso termino con errores.
    pause & exit /b %EXIT_CODE%
)

echo.
pause
exit /b 0

#@PY_START
import sys, base64, zipfile, re
from pathlib import Path

script_dir = Path(sys.argv[1])
out_path   = Path(sys.argv[2])
verify     = sys.argv[3] == '1'

ASSETS    = script_dir / 'assets'
FONTS_DIR = ASSETS / 'fonts'
TMPL_HTML = script_dir / 'template.html'

FONTS = {
    'FONT_THIN':             'SuraSans-Thin.otf',
    'FONT_THIN_ITALIC':      'SuraSans-ThinItalic.otf',
    'FONT_EXTRALIGHT':       'SuraSans-ExtraLight.otf',
    'FONT_EXTRALIGHT_ITALIC':'SuraSans-ExtraLightItalic.otf',
    'FONT_LIGHT':            'SuraSans-Light.otf',
    'FONT_LIGHT_ITALIC':     'SuraSans-LightItalic.otf',
    'FONT_REGULAR':          'SuraSans-Regular.otf',
    'FONT_ITALIC':           'SuraSans-Italic.otf',
    'FONT_SEMIBOLD':         'SuraSans-SemiBold.otf',
    'FONT_SEMIBOLD_ITALIC':  'SuraSans-SemiBoldItalic.otf',
    'FONT_BOLD':             'SuraSans-Bold.otf',
    'FONT_BOLD_ITALIC':      'SuraSans-BoldItalic.otf',
    'FONT_EXTRABOLD':        'SuraSans-ExtraBold.otf',
    'FONT_EXTRABOLD_ITALIC': 'SuraSans-ExtraBoldItalic.otf',
    'FONT_BLACK':            'SuraSans-Black.otf',
    'FONT_BLACK_ITALIC':     'SuraSans-BlackItalic.otf',
}

# Marcadores en el template.docx
MARKERS = [
    '__LC4_FECHA__',
    '__LC4_CUC__',
    '__LC4_EMPRESA__',
    '__LC4_REPRESENTANTES__',
    '__LC4_FACULTADES__',
    '__LC4_OBSERVACIONES__',
]

def b64(p):
    return base64.b64encode(p.read_bytes()).decode('ascii')

if verify:
    with zipfile.ZipFile(ASSETS / 'template.docx') as z:
        xml = z.read('word/document.xml').decode('utf-8')
    ok = True
    for m in MARKERS:
        count = xml.count(m)
        print(f"  {'OK' if count else 'FALTA'}  {m} ({count} ocurrencia/s)")
        if not count:
            ok = False
    print()
    print('Todos los marcadores encontrados.' if ok else 'Algunos marcadores no encontrados.')
    sys.exit(0 if ok else 1)

print('Leyendo template.html...')
html = TMPL_HTML.read_text(encoding='utf-8')

print('Encodificando fuentes Sura Sans (16 variantes)...')
for marker, filename in FONTS.items():
    p = FONTS_DIR / filename
    if not p.exists():
        print(f'  OMITIDA  {filename}')
        html = html.replace('{{' + marker + '}}', '')
    else:
        html = html.replace('{{' + marker + '}}', b64(p))
        print(f'  OK  {filename}')

print('Encodificando banner...')
html = html.replace('{{BANNER_B64}}', b64(ASSETS / 'banner.jpg'))
print('  OK  banner.jpg')

print('Encodificando plantilla docx...')
html = html.replace('{{TEMPLATE_B64}}', b64(ASSETS / 'template.docx'))
print('  OK  template.docx')

print('Inyectando librerias JS...')
html = html.replace('{{JSZIP}}',     (ASSETS / 'jszip.min.js').read_text(encoding='utf-8'))
html = html.replace('{{FILESAVER}}', (ASSETS / 'FileSaver.min.js').read_text(encoding='utf-8'))
print('  OK  jszip.min.js + FileSaver.min.js')

remaining = re.findall(r'\{\{[A-Z_]+\}\}', html)
if remaining:
    print(f'ADVERTENCIA -- Marcadores sin reemplazar: {remaining}')

out_path.write_text(html, encoding='utf-8')
print(f'\nOK  {out_path}  ({out_path.stat().st_size // 1024} KB)')
#@PY_END