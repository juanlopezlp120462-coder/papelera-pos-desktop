MERCADO PAGO - MOVIMIENTOS

Esta versión mantiene la consulta automática de pagos cada 15 segundos y agrega
una sección para obtener el reporte oficial "Todas las transacciones" de Mercado Pago.

- Pagos: consulta automática cada 15 segundos.
- Movimientos completos: genera e importa los últimos 7 días del reporte oficial.
- El reporte incluye movimientos que afectan el saldo, como pagos, ingresos,
  devoluciones, contracargos y retiros, según la información disponible en el
  reporte de Mercado Pago.
- El reporte de movimientos no es un canal de tiempo real: Mercado Pago lo genera
  de forma asíncrona. Para notificaciones realmente instantáneas se requiere un
  Webhook HTTPS en un servidor público.
- No compartir el Access Token.
