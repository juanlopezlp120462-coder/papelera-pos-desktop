WEBHOOK MERCADO PAGO - COTILLON POS

El POS inicia un receptor local en:
http://127.0.0.1:8765/webhook/mercadopago

Para Mercado Pago en modo productivo se necesita una URL HTTPS PUBLICA que apunte a ese endpoint.
Con Cloudflare Quick Tunnel:
cloudflared tunnel --url http://localhost:8765

Luego, en Mercado Pago > Webhooks > Productivo:
- URL de producción: tu URL HTTPS pública (se puede usar la raíz; el servidor acepta POST allí)
- Evento recomendado para la integración QR: Order (Mercado Pago)

IMPORTANTE SOBRE LA LLAVE SECRETA:
Mercado Pago indica que las notificaciones de Código QR no pueden validarse con la firma secreta.
Por eso el POS permite guardar la "Webhook Secret" en Configuración > Mercado Pago para
futuras notificaciones compatibles, pero no rechaza los eventos Order de QR por no tener una firma válida.

No compartas el Access Token ni la Webhook Secret.
La Quick Tunnel es temporal: si cerrás cloudflared, la URL deja de funcionar.
