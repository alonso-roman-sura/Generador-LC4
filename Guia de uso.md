# Generador LC4 - Guía de uso

**SURA Investments Perú - Cumplimiento Corporativo**

---

## Cómo abrir el generador

Hacer doble clic en `LC4_Generador.html`. Se abre en el navegador (Edge, Chrome o Firefox).

No requiere internet ni instalación de ningún programa. Todo el procesamiento ocurre en el equipo: ningún dato ingresado sale del dispositivo.

---

## Cómo generar un documento

### 1. Datos generales

| Campo | Descripción |
|---|---|
| **Fecha** | Se completa con la fecha de hoy. Cambiarla si corresponde a otra. Obligatorio. |
| **CUC** | Número de cliente en SURA. Opcional. |
| **Razón social** | Nombre completo de la empresa. Obligatorio. |

Si la razón social contiene caracteres que Windows no admite en nombres de archivo (`\ / : * ? " < > |`), se reemplazan por guiones al descargar.

### 2. Representantes / Apoderados

Agregar uno por cada persona que figure en la constitución o poder recibido.

- **Apellidos y nombres** - obligatorio
- **Cargo** - seleccionar del desplegable (Apoderado, Gerente General, Representante, Tesorero) o elegir "Otro" para escribir uno personalizado
- **Clase / Tipo** - solo la clase, sin repetir el cargo. Escribir `Clase A`, no `Apoderado Clase A`

Usar **+ Agregar representante** para añadir más y la **×** de la esquina para eliminar.

> Aquí solo se identifica a las personas. Quién firma con quién se define después, en Detalle de firmantes.

### 3. Detalle de firmantes

Hay dos modos, seleccionables con el toggle **Usar plantilla** / **Texto manual**.

#### Nombrar firmantes como

Antes de los bloques hay un selector que define cómo se nombra a los firmantes en el texto:

| Opción | Resultado en el documento |
|---|---|
| **Cargo** (por defecto) | el/la Apoderado Clase A |
| **Nombre** | PEREZ PEPITO |
| **Cargo y nombre** | el/la Apoderado Clase A (PEREZ PEPITO) |

La opción por defecto es la habitual en los LC4, porque las facultades corresponden al cargo y no a la persona. Conviene usar **Nombre** cuando dos personas comparten cargo y clase pero tienen facultades distintas.

El selector aplica a todo el documento, no a cada firmante por separado, para que la redacción sea uniforme.

#### Modo plantilla (recomendado)

Permite armar el detalle por bloques. Cada bloque describe quién puede hacer qué y bajo qué condición.

Al abrir el generador ya existe un bloque listo. Usar **+ Agregar bloque de actuación** por cada grupo adicional de firmantes con condiciones distintas.

Por cada bloque:

**a) Firmantes.** Hacer clic en los chips de los representantes que participan. Se ponen en negro al seleccionarse.

**b) Modalidad.**

- **A sola firma** - cada firmante seleccionado puede actuar independientemente
- **Mancomunada** - todos los firmantes seleccionados deben firmar juntos
- **Por grupos** - los firmantes se dividen en grupos y basta la firma de uno por grupo. Al elegirla aparece una fila por firmante para asignarlo al Grupo 1, 2 o 3
- **Combinación libre** - escribir la descripción en el campo de texto que aparece

Ejemplo de *Por grupos*: Grupo 1 = Gerente General o Tesorero, Grupo 2 = cualquier Apoderado Clase A. Significa que se necesita la firma de alguien del Grupo 1 junto con alguien del Grupo 2.

**c) Facultades.** Marcar las casillas de las facultades predefinidas que apliquen. El texto se construye automáticamente en el área de abajo.

Ese texto se puede editar libremente: lo escrito a mano no se pierde al cambiar la modalidad ni al seleccionar firmantes. Sí conviene tener en cuenta que **marcar o desmarcar una casilla vuelve a construir el texto desde las casillas**, así que es mejor marcar primero y editar después.

Una línea que empieza con `- ` sale como ítem de lista en Word. Sin el guion, sale como párrafo normal.

**Vista previa.** Al pie del panel aparece el texto exacto que quedará en el documento. Se actualiza conforme se completan los campos.

#### Modo texto manual

Para casos que no se pueden armar con la plantilla. Se escribe el detalle completo tal como debe aparecer y el generador lo inserta sin modificaciones.

### 4. Observaciones

Campo opcional para notas adicionales: límites de monto, vigencia u otras condiciones especiales. Cada línea se inserta como un párrafo independiente.

### 5. Generar el documento

Hacer clic en **GENERAR Y DESCARGAR LC4**. El archivo se descarga como `LC4 - {RAZÓN SOCIAL}.docx`.

Si falta algún campo obligatorio, el sistema lo marca en rojo. Cada bloque debe tener al menos un firmante seleccionado y sus facultades.

Antes de descargar, el generador verifica internamente que el documento sea válido. Si detecta algún problema lo informa en lugar de entregar un archivo dañado.

### 6. Obtener el PDF

El generador entrega un archivo Word. Para el PDF:

1. Abrir el documento descargado en Word
2. **Archivo › Guardar como ›** seleccionar PDF
3. Guardar

Se hace así a propósito. El documento se arma sobre la plantilla oficial en Word, y es Word quien decide los saltos de página, el ajuste de las tablas y la posición del sello. Convertir desde Word garantiza que el PDF sea idéntico al documento aprobado; un PDF generado por otra vía sería una aproximación, no el documento oficial.

Además, el LC4 lleva V°B° de Cumplimiento y de OPS, por lo que de todos modos pasa por una revisión en Word antes de archivarse.

---

## Preguntas frecuentes

**El archivo no descarga o sale un error en pantalla.**

El mensaje indica en qué etapa falló. Para más detalle, abrir la consola del navegador (tecla **F12**, pestaña Consola) y escribir:

```
LC4.diagnostico()
```

Indica exactamente qué falta para poder generar. Otros comandos disponibles:

| Comando | Qué hace |
|---|---|
| `LC4.estado()` | Muestra representantes, bloques y el texto que se escribirá |
| `LC4.verXml()` | Genera el documento sin descargarlo y verifica que sea válido |
| `LC4.ayuda()` | Lista los comandos |

Si el problema persiste, copiar lo que muestre la consola y enviarlo al equipo de Cumplimiento.

**El cargo que necesito no está en la lista.**

Seleccionar "Otro (especificar...)" en el desplegable y escribirlo manualmente.

**Necesito que dos representantes firmen juntos, pero uno puede hacerlo con cualquiera de tres opciones.**

Usar la modalidad **Por grupos**. Asignar al firmante fijo al Grupo 1 y las alternativas al Grupo 2.

**Quiero agregar un texto que no está en las facultades predefinidas.**

Escribirlo directamente en el área de texto del bloque, debajo de las casillas. Usar `- texto` para que aparezca como lista.

**¿Qué diferencia hay entre escribir una línea con `- ` y sin el guion?**

Con `- ` al inicio, la línea sale como ítem de lista en Word. Sin él, sale como párrafo normal. La vista previa muestra exactamente lo que se obtendrá.

**Escribí varias líneas en Observaciones. ¿Salen todas?**

Sí. Cada línea se inserta como un párrafo independiente.

**El área de facultades no crece y no veo todo el texto.**

Se ajusta automáticamente al contenido. Si no lo hace, probar con Chrome o Edge.

---

## Para el equipo de sistemas

El generador es un archivo HTML autocontenido. No requiere servidor ni instalación. Para distribuirlo basta con `LC4_Generador.html`.

### Estructura del proyecto

```
Modelo de Facultades de Apoderados\
├── build.bat            ejecutar con doble clic para recompilar
├── template.html        código fuente (con marcadores {{...}})
├── LC4_Generador.html   resultado del build
├── probar_lc4.py        banco de pruebas automatizadas
├── verificar_version.py comprueba que los archivos estén al día
└── assets\
    ├── template.docx    plantilla Word con marcadores __LC4_*__
    ├── banner.jpg
    ├── jszip.min.js
    ├── FileSaver.min.js
    └── fonts\           las 16 SuraSans-*.otf
```

### Qué tocar según el cambio

| Cambio deseado | Reemplazar | Ejecutar |
|---|---|---|
| Lógica, textos, interfaz | `template.html` | `build.bat` |
| Banner del encabezado | `assets\banner.jpg` | `build.bat` |
| Plantilla Word | `assets\template.docx` | `build.bat --verify` y luego `build.bat` |
| Nada, solo usar | - | nada |

`build.bat --verify` comprueba que los seis marcadores `__LC4_*__` sigan presentes en la plantilla. Conviene correrlo siempre que se reemplace el `.docx`, porque Word puede fragmentarlos al guardar.

### Pruebas automatizadas

```
pip install selenium
python probar_lc4.py
```

Abre el generador en Chrome, recorre once combinaciones, descarga los documentos y verifica que cada uno sea válido. Opciones: `--visible` para ver el navegador, `--caso N` para repetir uno, `--conservar` para no borrar los documentos.

Verifica que el archivo sea correcto, no cómo se ve. Conviene abrir un par en Word tras cada cambio importante.

### Advertencia sobre los archivos .bat

Los `.bat` deben guardarse con saltos de línea de Windows (CRLF). Con saltos de Unix, CMD parte los comandos a la mitad y falla con errores del tipo `"ocal" no se reconoce`. Algunos editores y herramientas de compresión los convierten silenciosamente.

`verificar_version.py` comprueba esto automáticamente.
