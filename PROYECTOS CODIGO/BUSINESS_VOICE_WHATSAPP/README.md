# Business Voice WhatsApp

Bot de voz para el WhatsApp de un negocio: lee los mensajes que entran, contesta
con Gemini y **manda la respuesta como nota de voz clonando una voz de
referencia**.

## Cómo funciona

1. **Playwright** abre WhatsApp Web (`headless=False`: hay que escanear el QR).
2. **Gemini 1.5 Flash** redacta la respuesta.
3. **Deep Translator** la pasa al idioma nativo del negocio (`NATIVE_LANGUAGE`,
   hoy `es`).
4. **Coqui TTS** la sintetiza clonando la voz de `sample.wav` y la deja en
   `generated_audio/`.

## Empezar

```bash
pip install -r requirements.txt
```

Necesita la variable de entorno `GOOGLE_API_KEY`. **Nunca la escribas en
`bot.py`** — el repo ignora `.env` y `*.token` justo para eso.

`sample.wav` debe tener ~10 segundos de voz limpia: es la muestra que se clona.

```bash
python bot.py
```

## Estado y siguiente paso

MVP funcionando. La hoja de ruta —y la deuda técnica que hay que pagar antes de
ponerlo en producción— está en [`FUTURE_PLAN.md`](FUTURE_PLAN.md).

## Aviso

Automatizar WhatsApp Web va contra los términos de servicio de WhatsApp y la
cuenta se puede bloquear. Para un negocio de verdad, el camino soportado es la
**WhatsApp Business API**. Esto es un prototipo.
