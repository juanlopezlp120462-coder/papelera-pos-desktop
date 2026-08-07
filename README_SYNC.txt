
PAPELERA POS - VERSION SYNC CLOUD - SIN MODIFICAR LOGICA

1. Tu programa original sigue igual: ejecuta EJECUTAR_PAPELERA.bat como siempre en la PC principal.

2. Para sincronizar con celular y otras PCs:
   a) Crea cuenta gratis en https://turso.tech
   b) turso db create papelera
   c) turso db show papelera -> copia URL
   d) turso db tokens create papelera -> copia token
   e) Edita ui/db.py y pega URL y TOKEN en TURSO_URL y TURSO_TOKEN

3. Luego ejecuta INICIAR_SYNC.bat
   - Te mostrara http://192.168.x.x:5000
   - Abri esa direccion en CUALQUIER celular conectado al mismo WiFi o en cualquier PC.
   - En el celular: Chrome > 3 puntitos > Agregar a pantalla de inicio -> queda como APP.

4. Todo lo que vendas en PC o celular se guarda en la nube y aparece en todos lados al instante.

Si queres que funcione fuera de tu WiFi (desde la calle, 4G), te lo subo a Render.com gratis y te queda con link https://...

DUDAS: El exe no puede ir directo al celular porque Android no ejecuta exe. Esta es la forma profesional que usan todos los POS.
