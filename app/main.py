"""Public, per-tab portfolio demo. All initial records are synthetic.

Deliberately has no database driver, environment loader, authentication, or
connection to the original application. Every request rebuilds fictional data.
"""
from decimal import Decimal
from datetime import date
from pathlib import Path
import re
import json
from jinja2 import pass_context

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
app = FastAPI(title="Expense Tracker · Portfolio Demo", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")

@pass_context
def money(ctx, value):
    formatted = f"{Decimal(str(value or 0)):,.2f}"
    if ctx.get('lang', 'en') == 'en':
        return '$ ' + formatted
    return "$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")

TRANSLATIONS = json.loads((ROOT / 'translations.json').read_text())

def localize(data, lang, edited_ids):
    if lang == 'es': return data
    if isinstance(data, list): return [localize(v, lang, edited_ids) for v in data]
    if isinstance(data, dict):
        return {k: v if k in {'description', 'note'} and
                (str(data.get('id', '')).startswith('demo-') or data.get('id') in edited_ids)
                else localize(v, lang, edited_ids) for k, v in data.items()}
    return TRANSLATIONS.get(data, data) if isinstance(data, str) else data

templates.env.filters["money"] = money
templates.env.globals.update(app_name="Finanzas · Demo", browser_title="Expense Tracker | Fictional Data Demo",
    database_status_label="Demo · Datos ficticios", app_tagline="Excel convertido en una app web")

MONTHS = [{"id": f"2026-{n:02d}", "label": f"{label} 2026", "n": n}
          for n, label in [(10,"Octubre"),(9,"Septiembre"),(8,"Agosto"),(7,"Julio"),(6,"Junio"),(5,"Mayo")]]
CATEGORIES = [{"id": i, "name": name, "color": color, "sort_order": i*10, "planned": planned}
 for i,name,color,planned in [(1,"Vivienda","#197C8C",900),(2,"Alimentación","#D49540",420),
 (3,"Transporte","#658BA4",180),(4,"Servicios","#8678A9",200),(5,"Salud","#559E83",130),
 (6,"Ocio","#B97C86",180)]]
PAYMENTS = [{"id":i,"name":n,"sort_order":i*10,"is_active":True} for i,n in [(1,"Transferencia"),(2,"Tarjeta"),(3,"Efectivo")]]
ACCOUNTS = [{"id":1,"name":"Banco demo","account_type":"bank","currency":"USD","opening_balance":1200,"sort_order":10,"is_active":True},
 {"id":2,"name":"Billetera demo","account_type":"wallet","currency":"USD","opening_balance":250,"sort_order":20,"is_active":True}]
CONTACTS = [{"id":i,"name":n,"party_type":t,"is_active":True,"tax_id":None,"email":None,"phone":None,"notes":"Contacto ficticio"}
 for i,n,t in [(1,"Cliente de ejemplo","client"),(2,"Mercado de ejemplo","supplier"),(3,"Servicios de ejemplo","supplier")]]

def transactions(month):
    factor = Decimal(100 + (month["n"]-5)*3) / 100
    entries = [(2,"Ingreso mensual de ejemplo",3200,None,"income",1,1,1),
        (3,"Alquiler de ejemplo",820,1,"expense",1,1,3),
        (5,"Compra semanal de ejemplo",78,2,"expense",2,1,2),
        (8,"Transporte mensual",92,3,"expense",3,2,None),
        (10,"Electricidad e internet",140,4,"expense",1,1,3),
        (12,"Compra semanal de ejemplo",85,2,"expense",2,1,2),
        (15,"Consulta de ejemplo",65,5,"expense",2,1,3),
        (18,"Actividad recreativa",70,6,"expense",3,2,None),
        (20,"Compra semanal de ejemplo",94,2,"expense",2,1,2),
        (22,"Servicio de ejemplo",260,None,"income",1,1,1),
        (25,"Compra semanal de ejemplo",79,2,"expense",2,1,2),
        (27,"Salida de ejemplo",48,6,"expense",3,2,None)]
    rows=[]
    for idx,(day,description,amount,cat,kind,payment,account,contact) in enumerate(entries):
        category = next((c for c in CATEGORIES if c["id"]==cat),{})
        rows.append(dict(id=f"{month['id']}-{idx}",transaction_date=f"{month['id']}-{day:02d}",description=description,
          amount=(Decimal(amount)*factor).quantize(Decimal("0.01")),kind=kind,category_id=cat,
          category_name=category.get("name"),category_color=category.get("color"),note="Dato ficticio · USD",
          payment_method_id=payment,payment_method_name=PAYMENTS[payment-1]["name"],account_id=account,
          account_name=ACCOUNTS[account-1]["name"],counterparty_id=contact,
          counterparty_name=CONTACTS[contact-1]["name"] if contact else None))
    return sorted(rows,key=lambda r:r["transaction_date"],reverse=True)

def summary(rows):
    income=sum((r["amount"] for r in rows if r["kind"]=="income"),Decimal(0))
    spent=sum((r["amount"] for r in rows if r["kind"]!="income"),Decimal(0))
    return income,spent

def context(month, operations=None):
    all_rows=[dict(r, month_id=m['id']) for m in MONTHS for r in transactions(m)]
    budgets={}
    for index,op in enumerate(operations or []):
        data=op.data
        if data.get('month_id') not in {m['id'] for m in MONTHS}:
            raise ValueError('Select a demo month.')
        if op.action=='budget':
            cid=int(data.get('category_id','0'))
            if cid not in {c['id'] for c in CATEGORIES}:
                raise ValueError('Invalid category.')
            budgets[(data['month_id'],cid)]=valid_amount(data.get('amount','0'),zero=True)
            continue
        target=next((r for r in all_rows if r['id']==op.id),None)
        if op.action=='delete':
            if target: all_rows.remove(target)
            continue
        if op.action=='edit' and not target:
            raise ValueError('Movement not found.')
        day=date.fromisoformat(data.get('transaction_date',''))
        if day.strftime('%Y-%m')!=data['month_id']:
            raise ValueError('La fecha debe pertenecer al mes seleccionado.')
        kind=data.get('kind','expense')
        if kind not in {'income','expense','extraordinary'}:
            raise ValueError('Invalid movement type.')
        amount=valid_amount(data.get('amount','0'))
        description=data.get('description','').strip()
        if not description or len(description)>120:
            raise ValueError('Description is required (maximum 120 characters).')
        row=dict(id=op.id if target else f'demo-{index}',month_id=data['month_id'],
            transaction_date=day.isoformat(),amount=amount,kind=kind,
            description=description,note=data.get('note','')[:240])
        for field,collection,prefix in [('category',CATEGORIES,'category'),('payment_method',PAYMENTS,'payment_method'),
            ('account',ACCOUNTS,'account'),('counterparty',CONTACTS,'counterparty')]:
            value=data.get(field+'_id','')
            item=next((r for r in collection if str(r['id'])==value),None)
            if value and not item: raise ValueError('Invalid reference.')
            row[prefix+'_id']=item['id'] if item else None
            row[prefix+'_name']=item['name'] if item else None
            if field=='category': row['category_color']=item['color'] if item else None
        if target: all_rows.remove(target)
        all_rows.append(row)
    rows=sorted([r for r in all_rows if r['month_id']==month['id']],key=lambda r:r['transaction_date'],reverse=True)
    income,spent=summary(rows)
    categories=[]
    for category in CATEGORIES:
        total=sum((r["amount"] for r in rows if r["category_id"]==category["id"]),Decimal(0))
        planned=budgets.get((month['id'],category['id']),Decimal(category['planned']))
        categories.append({**category,"planned":planned,"category_id":category["id"],"spent":total,
          "available":planned-total,"progress":total/planned if planned else None})
    budget=sum(c["planned"] for c in categories)
    maximum=max(income,budget,spent,1)
    accounts=[{**a,"movement_count":sum(r["account_id"]==a["id"] for r in all_rows),
      "current_balance":Decimal(a["opening_balance"])+sum((r["amount"]*(1 if r["kind"]=="income" else -1)
        for r in all_rows if r["account_id"]==a["id"]),Decimal(0))} for a in ACCOUNTS]
    contacts=[{**c,"movement_count":sum(r["counterparty_id"]==c["id"] for r in all_rows)} for c in CONTACTS]
    payments=[{**p,"usage_count":sum(r["payment_method_id"]==p["id"] for r in all_rows)} for p in PAYMENTS]
    trend=[]
    for m in reversed(MONTHS):
        inc,exp=summary([r for r in all_rows if r['month_id']==m['id']])
        trend.append(dict(label=m["label"],income=inc,expense=exp))
    peak=max(max(r["income"],r["expense"]) for r in trend) or 1
    for t in trend:
        t.update(income_width=100*t["income"]/peak,expense_width=100*t["expense"]/peak)
    expenses=[r for r in rows if r["kind"]!="income"]
    reports=dict(kpis=dict(income=income,expense=spent,net=income-spent,
      average_expense=spent/len(expenses) if expenses else 0,transaction_count=len(rows)),
      by_category=[dict(label=c["name"],color=c["color"],amount=c["spent"],percentage=c["spent"]/spent if spent else 0) for c in categories],
      by_payment_method=[dict(label=p["name"],movement_count=sum(r["payment_method_id"]==p["id"] for r in expenses),
        amount=sum((r["amount"] for r in expenses if r["payment_method_id"]==p["id"]),Decimal(0))) for p in PAYMENTS],
      by_account=[dict(label=a["name"],movement_count=sum(r["account_id"]==a["id"] for r in rows),
        net=sum((r["amount"]*(1 if r["kind"]=="income" else -1) for r in rows if r["account_id"]==a["id"]),Decimal(0))) for a in ACCOUNTS],
      by_counterparty=[dict(label=c["name"],party_type=c["party_type"],movement_count=sum(r["counterparty_id"]==c["id"] for r in rows),
        amount=sum((r["amount"] for r in rows if r["counterparty_id"]==c["id"]),Decimal(0))) for c in CONTACTS],trend=trend)
    return dict(months=MONTHS,selected_month=month,movements=rows,categories=CATEGORIES,accounts=accounts,
      counterparties=contacts,payment_methods=payments,reports=reports,
      dashboard=dict(kpis=dict(income=income,budget=budget,spent=spent,balance=income-spent),
      chart_heights=[max(2,int(100*v/maximum)) for v in [income,budget,spent]],categories=categories,recent=rows[:5]))

@app.middleware("http")
async def read_only(request,call_next):
    if request.method not in ("GET","HEAD") and not (request.method=='POST' and request.url.path=='/demo/render'):
        return HTMLResponse("Demo only. No data is stored.",status_code=405,headers={"Allow":"GET, HEAD"})
    if request.url.path=='/demo/render' and len(await request.body())>150000:
        return HTMLResponse('Demo limit reached. Reset to continue.',status_code=413)
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["X-Robots-Tag"]="noindex, nofollow"
    return response

@app.get("/")
def home():
    return RedirectResponse("/dashboard")

@app.get("/health")
def health():
    return {"status":"ok","mode":"synthetic-per-tab","database":False,"reset_minutes":60}

def valid_amount(raw,zero=False):
    value=Decimal(raw)
    if not value.is_finite() or value<0 or value>1000000 or (not zero and value==0):
        raise ValueError('Use an amount between 0.01 and 1,000,000.')
    return value.quantize(Decimal('0.01'))

class Operation(BaseModel):
    action: str=Field(pattern='^(create|edit|delete|budget)$')
    id: str=''
    data: dict[str,str]

class RenderRequest(BaseModel):
    page: str
    lang: str=Field(default='en', pattern='^(en|es)$')
    month_id: str|None=None
    operations: list[Operation]=Field(default_factory=list,max_length=200)

@app.post('/demo/render',response_class=HTMLResponse)
def render_demo(request:Request,body:RenderRequest):
    try:
        return render_page(request,body.page,body.month_id,body.operations,body.lang)
    except (ValueError,ArithmeticError) as error:
        raise HTTPException(422,detail=str(error)) from error

@app.get("/{page}",response_class=HTMLResponse)
def page(request:Request,page:str,month_id:str|None=None,lang:str='en'):
    return render_page(request,page,month_id,lang=lang)

def render_page(request,page,month_id,operations=None,lang='en'):
    lang = 'es' if lang == 'es' else 'en'
    translate = lambda text: TRANSLATIONS.get(text, text) if lang == 'en' else text
    template=page.replace("-","_")
    if template not in {"dashboard","movements","reports","budgets","accounts","contacts","categories","payment_methods"}:
        raise HTTPException(404)
    month=next((m for m in MONTHS if m["id"]==month_id),MONTHS[0])
    data = localize(context(month,operations), lang, {op.id for op in operations or [] if op.action=='edit'})
    html=templates.get_template(template+".html").render(request=request,active_page=template,
        lang=lang,t=translate,app_name=translate('Finanzas · Demo'),
        database_status_label=translate('Demo · Datos ficticios'),**data)
    # Catalogs are viewable; only transactions and budgets are editable in this demo.
    def disable_write_form(match):
        if re.search(r'action="/(movements|budgets)|data-movement-edit-form',match[1]):
            return match[0]
        body=re.sub(r'<(input|select|textarea)\b',r'<\1 disabled',match[2])
        body=re.sub(r'<button\b(?=[^>]*type="submit")','<button disabled',body)
        return match[1]+body+'</form>'
    html=re.sub(r'(<form\b[^>]*method="post"[^>]*>)(.*?)</form>',disable_write_form,html,flags=re.S)
    return HTMLResponse(html)
