# 🔧 Conectar IndieStudio con GitHub — Instrucciones (una sola vez)

Sigue estos pasos UNA VEZ y después todo se sube automáticamente.

---

## PASO 1 — Crear tu token de GitHub

1. Ve a: https://github.com/settings/tokens/new
2. Dale un nombre: `Indie-Junior-Projects-token`
3. En **Expiration**: selecciona `No expiration`
4. En **Select scopes**: marca `repo` (el primero, incluye todo lo de repos)
5. Haz clic en **Generate token**
6. **COPIA EL TOKEN** — solo lo verás una vez

---

## PASO 2 — Crear el repositorio en GitHub

1. Ve a: https://github.com/new
2. Nombre: `Indie-Junior-Projects`
3. Descripción: `Game dev portfolio — Monterrey | UANL | Indie Developer`
4. Selecciona **Public** (para que los reclutadores lo vean)
5. **NO** marques "Add README" (ya tenemos uno)
6. Haz clic en **Create repository**

---

## PASO 3 — Guardar el token en tu computadora

Abre **PowerShell** (busca "PowerShell" en el menú de inicio) y ejecuta:

```powershell
# Reemplaza TU_TOKEN y TU_USUARIO con tus datos reales
$token = "TU_TOKEN_AQUI"
$usuario = "TU_USUARIO_GITHUB"

# Guardar token (solo en tu computadora, nunca se sube a GitHub)
Set-Content -Path "$env:USERPROFILE\Desktop\IndieStudio\.github_token" -Value "$usuario`:$token"

# Configurar git
cd "$env:USERPROFILE\Desktop\IndieStudio"
git config user.name "TU_NOMBRE"
git config user.email "brunich99@gmail.com"
git remote add origin "https://$token@github.com/$usuario/Indie-Junior-Projects.git"
git branch -M main
git add .
git commit -m "🎮 Inicio IndieStudio - primer commit"
git push -u origin main

Write-Host "✅ ¡Listo! Tu repo está en GitHub."
```

---

## PASO 4 — Verificar

Abre: `https://github.com/TU_USUARIO/Indie-Junior-Projects`

Deberías ver todos los archivos de tu carpeta IndieStudio.

---

## Después de la configuración inicial

Cada vez que los agentes generen archivos nuevos, el **Agente GitHub**
(que corre a las 9pm) hará el commit y push automáticamente.

Si quieres hacer push manual en cualquier momento, abre PowerShell:
```powershell
cd "$env:USERPROFILE\Desktop\IndieStudio"
git add .
git commit -m "update: [fecha]"
git push
```

---

*Una vez que completes estos pasos, díselo a Claude en Cowork para activar los push automáticos.*
