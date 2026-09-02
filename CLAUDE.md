# codigos — reglas que se leen ANTES de tocar nada

Este repo (`Brunich/Indie-Junior-Projects`) guarda **varios proyectos independientes**.
El índice de qué es cada uno está en [`README.md`](README.md).

**Entra a la carpeta del proyecto que te toca y lee su `CLAUDE.md`. No leas los
demás.** Aquí sólo va lo que vale para todos.

---

## 🔍 EL NOMBRE MIENTE. COMPRUEBA EL CONTENIDO

La trampa más cara de este repo, medida el 01-09-2026 sobre los proyectos que
más documentación tenían:

- **NEXOS**: su `CLAUDE.md` mandaba leer **9 documentos que no existen** y daba
  por implementados **6 ficheros que no están en el disco**. Y encima la carpeta
  entera era una copia vieja: el proyecto vive en `Brunich/Nexos`, tres meses
  más al día. Por eso ya no está aquí.
- **PLATAFORMERO_2D**: `project.godot` declara **4 autoloads que no pueden
  cargar** — dos por una ruta imposible (`res://../../`), y dos porque el
  fichero no existe. El README documenta con ejemplos de uso un `AudioManager`
  que nunca se escribió.
- **AUTOCHART**: había **dos carpetas** con el mismo README. La segunda resultó
  ser una copia de la rama `editor/tocar-y-grabar`, con PR abierto — no un
  proyecto. **Lo comprobé comparándola contra la rama, no leyendo su README.**

**La regla:** antes de construir encima de algo que un documento da por hecho,
haz `ls`. **Un `✅` en un Markdown no es prueba de que el fichero exista.** Y si
descubres que un documento miente, **corrige el documento en la misma tanda** —
si no, la siguiente IA paga el mismo peaje.

---

## 🖼️ LO PESADO NO ENTRA EN GIT, Y SE DICE POR QUÉ

Un binario commiteado **se queda en el historial para siempre**, aunque después
lo borres. Por eso [`.gitignore`](.gitignore) lleva la razón escrita al lado de
cada regla, no sólo el patrón.

Hoy quedan fuera, a propósito:

| Qué | Por qué |
|---|---|
| `NEXOS/` | Tiene **repo propio y más al día**: `Brunich/Nexos` (jun-2026 contra abr-2026 de la copia local). Y su `world_building_tiles/` son 442 MB en 126 PNG con duplicados |
| `AUTOCHART/` | Tiene **repo propio**: `Brunich/clonehero-autochart`. Su `salida/` son **9,9 GB** |
| `salida/`, `output/`, `__pycache__/`, `.godot/` | Se regenera con el comando |

**Y el matiz que importa:** si el código **vuelve a leer** esa ruta
(`load()`, `preload()`, `FileAccess.open(..., READ)`, `Image.load()`), entonces
no es salida, **es un asset** — y dejarlo fuera de git rompe algo para quien
clone. Cuando pase, **se escribe en el `CLAUDE.md` del proyecto**, no se deja
que se rompa en silencio.

---

## 📦 UN PROYECTO CON REPO PROPIO NO SE ANIDA AQUÍ

`AUTOCHART` y `NEXOS` tienen el suyo, y **IA Rogue** también
(`Brunich/IA-Rogue-DEFINITIVE`). Meterlos dentro de este crea un *gitlink* roto
—en GitHub sale una carpeta gris que no se abre— y, peor, **dos copias que se
van separando sin que nadie sepa cuál manda**. Es exactamente lo que había
pasado con NEXOS: la copia local era de abril y el repo propio de junio.

Los tres están ignorados aquí y enlazados desde el `README.md`.

Si mañana otro proyecto se independiza, **el mismo tratamiento**: ignorar la
carpeta y enlazar el repo desde el índice.

---

## 🏷️ LAS CARPETAS SE LLAMAN POR SU NOMBRE, SIN NÚMERO

Desde el 01-09-2026: `NEXOS`, no `05_NEXOS`. `PONG`, no `01_PONG`.

Los números decían el orden en que se empezaron —que a nadie le sirve— y encima
chocaban: había **dos `06_`**. Si añades un proyecto, **nombre y ya**.

Al renombrar hay que arreglar lo que apunta al nombre viejo. En la tanda del
01-09 había 5 referencias vivas, una de ellas en código (una ruta absoluta a una
carpeta `IA TEAM/` que ya no existía). **Los reportes y QA con fecha en
`_SHARED/` NO se tocan**: son historia, no punteros.

---

## 🔐 EL TOKEN DE GITHUB

Vive en `CONFIG/.github_token` y está en `.gitignore`. **Nunca se escribe una
clave dentro de un `.py` ni de un `.md`.** Los proyectos de Python leen sus
claves de variables de entorno (`GOOGLE_API_KEY` y compañía).

**Arreglado el 01-09-2026:** el `origin` llevaba el token **incrustado en la
URL** (`https://Brunich:ghp_...@github.com/...`). No viajaba a GitHub
—`.git/config` no se sube— pero **cualquiera que mirase la consola lo veía**, y
salía entero en cada `git remote -v`. Ahora el remote es la URL limpia
(`https://github.com/Brunich/Indie-Junior-Projects.git`) y quien autentica es el
credential helper `manager` de Windows, que ya estaba configurado. Comprobado
con un `git ls-remote` y con el push de la rama.

**No lo vuelvas a poner en la URL.** Si el push pide credenciales, es que el
helper perdió la entrada: se arregla con `gh auth login`, no metiendo el token
en el remote.

El token que estaba en esa URL **Bruno ya lo revocó** (01-09-2026). Si
`CONFIG/.github_token` sigue teniéndolo, ese fichero está muerto: se reescribe
con uno nuevo o se borra si ya no se usa el `.bat`.

---

## 🔄 `git fetch` ANTES DE RAMIFICAR. SIEMPRE

Medido el 01-09-2026, y me pasó a mí: ramifiqué desde `main` local sin traer el
remoto, y `git rev-list --count origin/main...HEAD` respondió **contra un
`origin/main` viejo** — dijo «0 detrás» cuando en GitHub había **4 commits que no
tenía**: Pong jugable, el Space Shooter entero y un ROGUELIKE completo.

Consecuencia: documenté `SPACE_SHOOTER` como «vacío, nunca se empezó» **cuando
en GitHub había un juego funcionando**, y el PR salió en conflicto.

**La regla:** `git fetch` antes de mirar `origin/*`. Un ref de seguimiento sin
fetch **no es el remoto**, es la última foto que se tomó de él — y no avisa de
que está vieja.

---

## Antes de cerrar una tanda

1. **Comprobado, no supuesto.** Si dices que algo funciona, es porque lo
   ejecutaste o lo miraste. Si no pudiste, dilo.
2. **El documento que mentía queda corregido**, no anotado para después.
3. **Commit, push y PR.** Un commit sin push no existe para nadie más.
4. **Sin basura.** Lo generado no se commitea; se rehace con el comando que
   quede documentado al lado.
