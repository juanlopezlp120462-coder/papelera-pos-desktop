import json, urllib.request, urllib.parse, urllib.error, datetime, sqlite3, os, csv, io, time

API_URL = "https://api.mercadopago.com/v1/payments/search"
REPORT_URL = "https://api.mercadopago.com/v1/account/settlement_report"

def _db_path():
    from ui.db import BASE_DATOS, init_db
    init_db()
    return BASE_DATOS

def _request_json(url, token, params=None, method="GET", body=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    headers={"Authorization":"Bearer "+token,"Accept":"application/json","Content-Type":"application/json","User-Agent":"PAPELERA-POS/1.1"}
    data=None if body is None else json.dumps(body).encode("utf-8")
    req=urllib.request.Request(url,headers=headers,method=method,data=data)
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail=e.read().decode("utf-8","replace")
        try: detail=json.loads(detail)
        except Exception: pass
        raise RuntimeError(f"Mercado Pago HTTP {e.code}: {detail}")


def listar_cuentas():
    from ui.db import get_setting
    try:
        cuentas=json.loads(get_setting('mp_accounts','[]') or '[]')
        return cuentas if isinstance(cuentas,list) else []
    except Exception:
        return []

def guardar_cuentas(cuentas, activo=0):
    from ui.db import set_setting
    set_setting('mp_accounts', json.dumps(cuentas, ensure_ascii=False))
    set_setting('mp_active_account', str(max(0,int(activo))))

def token_activo():
    from ui.db import get_setting
    cuentas=listar_cuentas()
    try:i=int(get_setting('mp_active_account','0') or 0)
    except Exception:i=0
    if cuentas and 0 <= i < len(cuentas):
        return str(cuentas[i].get('token','')).strip()
    return get_setting('mp_access_token','').strip()

def nombre_cuenta_activa():
    from ui.db import get_setting
    cuentas=listar_cuentas()
    try:i=int(get_setting('mp_active_account','0') or 0)
    except Exception:i=0
    if cuentas and 0 <= i < len(cuentas): return str(cuentas[i].get('nombre') or f'Cuenta {i+1}')
    return 'Cuenta principal'

def buscar_pago_aprobado_por_importe(token, importe, desde=None, tolerancia=0.01):
    """Busca un pago aprobado reciente que coincida con el importe.
    Se usa para confirmar cobros de transferencias/QR sin depender de un webhook publico."""
    token=(token or '').strip()
    if not token: return None
    ahora=datetime.datetime.now(datetime.timezone.utc)
    if desde is None: desde=ahora-datetime.timedelta(minutes=10)
    if desde.tzinfo is None: desde=desde.replace(tzinfo=datetime.timezone.utc)
    params={'sort':'date_created','criteria':'desc','range':'date_created',
            'begin_date':desde.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'end_date':ahora.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'limit':'50','offset':'0'}
    data=_request_json(API_URL,token,params)
    for p in (data.get('results',[]) if isinstance(data,dict) else []):
        estado=str(p.get('status') or '').lower()
        try:monto=float(p.get('transaction_amount') or 0)
        except Exception:monto=0
        if estado in ('approved','accredited') and abs(monto-float(importe)) <= float(tolerancia):
            return p
    return None

def _request_bytes(url, token):
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"*/*","User-Agent":"PAPELERA-POS/1.1"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail=e.read().decode("utf-8","replace")
        raise RuntimeError(f"Mercado Pago HTTP {e.code}: {detail}")

def buscar_pagos(token,dias=30,limite=50):
    token=(token or "").strip()
    if not token: raise ValueError("Falta el Access Token de Mercado Pago.")
    ahora=datetime.datetime.now(datetime.timezone.utc); inicio=ahora-datetime.timedelta(days=int(dias))
    params={"sort":"date_created","criteria":"desc","range":"date_created",
            "begin_date":inicio.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "end_date":ahora.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "limit":str(min(int(limite),50)),"offset":"0"}
    data=_request_json(API_URL,token,params)
    return data.get("results",[]) if isinstance(data,dict) else []

def guardar_pagos(pagos):
    con=sqlite3.connect(_db_path())
    try:
        for p in pagos:
            pid=str(p.get("id",""))
            if not pid: continue
            fecha=p.get("date_created") or p.get("date_approved") or ""
            estado=str(p.get("status") or "").upper()
            importe=float(p.get("transaction_amount") or 0)
            medio=str(p.get("payment_method_id") or p.get("payment_type_id") or "Mercado Pago")
            detalle=str(p.get("description") or "")
            con.execute("""INSERT INTO mp_comprobantes
            (id,fecha,estado,importe,operacion,medio,detalle,actualizado_en)
            VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET fecha=excluded.fecha,estado=excluded.estado,
            importe=excluded.importe,medio=excluded.medio,detalle=excluded.detalle,
            actualizado_en=excluded.actualizado_en""",
            (pid,fecha,estado,importe,pid,medio,detalle,datetime.datetime.now().isoformat(timespec="seconds")))
        con.commit()
    finally: con.close()

def ultimos_guardados(limite=100):
    con=sqlite3.connect(_db_path())
    try:
        return con.execute("""SELECT id,fecha,estado,importe,operacion,medio,detalle
        FROM mp_comprobantes ORDER BY datetime(fecha) DESC LIMIT ?""",(int(limite),)).fetchall()
    finally: con.close()

def probar_token(token):
    return buscar_pagos(token,dias=1,limite=1)

def _report_headers(token):
    return {"Authorization":"Bearer "+token,"Accept":"application/json","Content-Type":"application/json","User-Agent":"PAPELERA-POS/1.1"}

def configurar_reporte(token):
    """Asegura una configuración de Todas las transacciones que incluya retiros."""
    h=_report_headers(token)
    try:
        req=urllib.request.Request(REPORT_URL+"/config",headers=h,method="GET")
        with urllib.request.urlopen(req,timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code != 404: raise
    body={
        "file_name_prefix":"papelera-pos",
        "show_fee_prevision":True,"show_chargeback_cancel":True,
        "include_withdraw":True,"shipping_detail":True,"refund_detailed":True,
        "coupon_detailed":True,"display_timezone":"GMT-03","header_language":"es",
        "columns":[{"key":"TRANSACTION_DATE"},{"key":"SOURCE_ID"},{"key":"EXTERNAL_REFERENCE"}]
    }
    req=urllib.request.Request(REPORT_URL+"/config",headers=h,method="POST",data=json.dumps(body).encode())
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read().decode())

def crear_reporte_movimientos(token,begin_date,end_date):
    configurar_reporte(token)
    body={"begin_date":begin_date,"end_date":end_date}
    h=_report_headers(token)
    req=urllib.request.Request(REPORT_URL,headers=h,method="POST",data=json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail=e.read().decode("utf-8","replace")
        raise RuntimeError(f"Mercado Pago HTTP {e.code}: {detail}")

def estado_reporte(token,task_id):
    return _request_json(REPORT_URL+"/task/"+str(task_id),token,{"access_token":token})

def descargar_reporte(token,file_name):
    return _request_bytes(REPORT_URL+"/"+urllib.parse.quote(str(file_name),safe=""))

def _parse_money(v):
    if v is None:return 0.0
    s=str(v).strip().replace("$","").replace(" ","")
    if not s:return 0.0
    # Reportes ES suelen usar 1.234,56; también aceptamos 1234.56.
    if "," in s and "." in s:s=s.replace(".","").replace(",",".")
    elif "," in s:s=s.replace(",",".")
    try:return float(s)
    except:return 0.0

def importar_csv_movimientos(data):
    text=data.decode("utf-8-sig","replace")
    sample=text[:5000]
    try: dialect=csv.Sniffer().sniff(sample,delimiters=",;|\t")
    except Exception: dialect=csv.excel
    rows=list(csv.DictReader(io.StringIO(text),dialect=dialect))
    if not rows:return 0
    def pick(row,*names):
        for n in names:
            if n in row:return row.get(n)
            for k in row:
                if k.strip().upper()==n.upper():return row.get(k)
        return ""
    con=sqlite3.connect(_db_path()); count=0
    try:
        for row in rows:
            rid=str(pick(row,"SOURCE_ID","SOURCE ID","ID","SOURCE_ID") or pick(row,"EXTERNAL_REFERENCE","EXTERNAL REFERENCE"))
            fecha=str(pick(row,"TRANSACTION_DATE","TRANSACTION DATE","DATE","DATE_CREATED") or "")
            tipo=str(pick(row,"TRANSACTION_TYPE","TRANSACTION TYPE","OPERATION_TYPE","TYPE") or "")
            importe=_parse_money(pick(row,"TRANSACTION_AMOUNT","TRANSACTION AMOUNT","GROSS_AMOUNT","AMOUNT"))
            neto=_parse_money(pick(row,"NET_CREDIT_AMOUNT","NET CREDIT AMOUNT","NET_AMOUNT","NET AMOUNT"))
            ref=str(pick(row,"EXTERNAL_REFERENCE","EXTERNAL REFERENCE","REFERENCE") or "")
            desc=str(pick(row,"DESCRIPTION","DETAIL","OPERATION") or "")
            estado=str(pick(row,"STATUS","STATUS_DESCRIPTION","STATUS DESCRIPTION") or "APROBADO")
            if not rid: rid=f"{fecha}|{ref}|{importe}|{desc}"
            con.execute("""INSERT INTO mp_movimientos
            (id,fecha,tipo,importe,neto,referencia,descripcion,estado,actualizado_en,fuente)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET fecha=excluded.fecha,tipo=excluded.tipo,
            importe=excluded.importe,neto=excluded.neto,referencia=excluded.referencia,
            descripcion=excluded.descripcion,estado=excluded.estado,
            actualizado_en=excluded.actualizado_en,fuente=excluded.fuente""",
            (rid,fecha,tipo,importe,neto,ref,desc,estado,datetime.datetime.now().isoformat(timespec="seconds"),"Account Money Report"))
            count+=1
        con.commit()
    finally: con.close()
    return count

def ultimos_movimientos(limite=200):
    con=sqlite3.connect(_db_path())
    try:
        return con.execute("""SELECT id,fecha,tipo,importe,neto,referencia,descripcion,estado,fuente
        FROM mp_movimientos ORDER BY datetime(fecha) DESC LIMIT ?""",(int(limite),)).fetchall()
    finally: con.close()
