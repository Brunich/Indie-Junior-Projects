# WhatsApp Ticket Hunter

Vigila los chats de WhatsApp Web sin leer, busca mensajes con entradas
disponibles y contesta.

## Cómo funciona

**Playwright** abre `web.whatsapp.com` con `headless=False` y espera
indefinidamente (`timeout=0`) a que escanees el QR. A partir de ahí trabaja
sobre tres selectores del DOM:

```
UNREAD_BADGE_SELECTOR   burbuja de "no leído" (inglés y español)
MESSAGE_IN_SELECTOR     texto de los mensajes entrantes
CHAT_BOX_SELECTOR       la caja de escribir
```

## La trampa conocida

**Esos tres selectores son el punto frágil de todo el proyecto.** WhatsApp Web
cambia su DOM cada pocas semanas y el bot deja de ver los mensajes sin dar
error: simplemente no encuentra nada. Si un día "no hace nada", **empieza por
inspeccionar la página y actualizar los selectores de arriba**, no por revisar
la lógica.

El propio fichero lo avisa en su cabecera. La hoja de ruta en
[`FUTURE_PLAN.md`](FUTURE_PLAN.md) apunta justo ahí: quitar la dependencia del
DOM.

## Empezar

```bash
pip install -r requirements.txt
python hunter.py
```

No guarda sesión: hay que escanear el QR cada vez. Un `persistent_context` de
Playwright lo arreglaría — está anotado como pendiente en el código.

## Aviso

Automatizar WhatsApp Web va contra sus términos de servicio y la cuenta se
puede bloquear. Es un prototipo.
