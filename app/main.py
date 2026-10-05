from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, os
from datetime import date

DB=os.getenv('DB_PATH','/data/tasks.db')
os.makedirs(os.path.dirname(DB), exist_ok=True)
app=FastAPI(title='Everest IT Task Manager')
app.mount('/static', StaticFiles(directory='/app/static'), name='static')

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=db(); c.execute('''CREATE TABLE IF NOT EXISTS tasks(
      id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT,
      category TEXT,priority TEXT,status TEXT,assignee TEXT,due_date TEXT,
      follow_up TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,completed_at TEXT)'''); c.commit(); c.close()
init()

CATS=['Infrastructure','Network','Security','Microsoft 365','SAP','Hardware','Procurement','User Support','IT Governance','Automation','Projects']
PR=['Critical','High','Medium','Low']; ST=['New','In Progress','Waiting','Completed','Cancelled']

def page(body):
    return f'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Everest IT Task Manager</title><link rel="stylesheet" href="/static/style.css"></head><body><header><div><b>EVEREST</b><span> IT Task Manager</span></div><a href="/">Dashboard</a><a href="/tasks">Tasks</a><a href="/new">+ New Task</a></header><main>{body}</main></body></html>'''

@app.get('/',response_class=HTMLResponse)
def home():
    c=db(); rows=c.execute('select * from tasks order by case priority when "Critical" then 1 when "High" then 2 when "Medium" then 3 else 4 end, due_date').fetchall(); c.close()
    today=str(date.today()); total=len(rows); completed=sum(r['status']=='Completed' for r in rows); overdue=sum(r['due_date'] and r['due_date']<today and r['status'] not in ('Completed','Cancelled') for r in rows); follow=sum(bool(r['follow_up']) and r['status']!='Completed' for r in rows)
    cards=''.join([f'<div class="card"><small>{label}</small><strong>{val}</strong></div>' for label,val in [('Total',total),('Completed',completed),('Overdue',overdue),('Follow-up',follow)]])
    trs=''.join(f'<tr><td><a href="/task/{r["id"]}">{r["title"]}</a></td><td>{r["category"] or "-"}</td><td><span class="p {r["priority"].lower()}">{r["priority"]}</span></td><td>{r["status"]}</td><td>{r["due_date"] or "-"}</td></tr>' for r in rows[:12]) or '<tr><td colspan="5">No tasks yet.</td></tr>'
    return page(f'<h1>IT Management Dashboard</h1><div class="cards">{cards}</div><section><div class="sectionhead"><h2>Priority Work</h2><a class="btn" href="/new">Create task</a></div><table><thead><tr><th>Task</th><th>Category</th><th>Priority</th><th>Status</th><th>Due</th></tr></thead><tbody>{trs}</tbody></table></section>')

@app.get('/tasks',response_class=HTMLResponse)
def tasks(q:str='',status:str='',priority:str=''):
    c=db(); sql='select * from tasks where 1=1'; args=[]
    if q: sql+=' and (title like ? or description like ?)'; args += [f'%{q}%',f'%{q}%']
    if status: sql+=' and status=?'; args.append(status)
    if priority: sql+=' and priority=?'; args.append(priority)
    sql+=' order by due_date is null, due_date'; rows=c.execute(sql,args).fetchall(); c.close()
    trs=''.join(f'<tr><td><a href="/task/{r["id"]}">{r["title"]}</a></td><td>{r["category"] or "-"}</td><td><span class="p {r["priority"].lower()}">{r["priority"]}</span></td><td>{r["status"]}</td><td>{r["assignee"] or "-"}</td><td>{r["due_date"] or "-"}</td></tr>' for r in rows) or '<tr><td colspan="6">No matching tasks.</td></tr>'
    form=f'''<form class="filters"><input name="q" value="{q}" placeholder="Search tasks..."><select name="status"><option value="">All status</option>{''.join(f'<option {"selected" if status==s else ""}>{s}</option>' for s in ST)}</select><select name="priority"><option value="">All priority</option>{''.join(f'<option {"selected" if priority==p else ""}>{p}</option>' for p in PR)}</select><button>Filter</button></form>'''
    return page(f'<div class="sectionhead"><h1>Tasks</h1><a class="btn" href="/new">+ New Task</a></div>{form}<section><table><thead><tr><th>Task</th><th>Category</th><th>Priority</th><th>Status</th><th>Assignee</th><th>Due</th></tr></thead><tbody>{trs}</tbody></table></section>')

@app.get('/new',response_class=HTMLResponse)
def new(): return page(form_html(None))

def form_html(r):
    r=r or {}; val=lambda k:r[k] if isinstance(r,sqlite3.Row) and r[k] is not None else ''
    opts=lambda items,key: ''.join(f'<option {"selected" if val(key)==x else ""}>{x}</option>' for x in items)
    return f'''<section class="formbox"><h1>{'Edit Task' if r else 'New Task'}</h1><form method="post" action="{'/task/'+str(r['id'])+'/edit' if r else '/new'}"><label>Task title<input name="title" required value="{val('title')}"></label><label>Description<textarea name="description">{val('description')}</textarea></label><div class="grid"><label>Category<select name="category">{opts(CATS,'category')}</select></label><label>Priority<select name="priority">{opts(PR,'priority')}</select></label><label>Status<select name="status">{opts(ST,'status')}</select></label><label>Assignee<input name="assignee" value="{val('assignee')}" placeholder="Person / vendor"></label><label>Due date<input type="date" name="due_date" value="{val('due_date')}"></label><label>Follow-up date<input type="date" name="follow_up" value="{val('follow_up')}"></label></div><button class="btn">Save Task</button></form></section>'''

@app.post('/new')
def create(title:str=Form(...),description:str=Form(''),category:str=Form(''),priority:str=Form('Medium'),status:str=Form('New'),assignee:str=Form(''),due_date:str=Form(''),follow_up:str=Form('')):
    c=db(); c.execute('insert into tasks(title,description,category,priority,status,assignee,due_date,follow_up) values(?,?,?,?,?,?,?,?)',(title,description,category,priority,status,assignee,due_date,follow_up)); c.commit(); c.close(); return RedirectResponse('/',303)

@app.get('/task/{tid}',response_class=HTMLResponse)
def detail(tid:int):
    c=db(); r=c.execute('select * from tasks where id=?',(tid,)).fetchone(); c.close()
    if not r: return HTMLResponse(page('<h1>Task not found</h1>'),404)
    return page(f'<section><div class="sectionhead"><h1>{r["title"]}</h1><a class="btn" href="/task/{tid}/edit">Edit</a></div><div class="detail"><p><b>Category:</b> {r["category"] or "-"}</p><p><b>Priority:</b> {r["priority"]}</p><p><b>Status:</b> {r["status"]}</p><p><b>Assignee:</b> {r["assignee"] or "-"}</p><p><b>Due:</b> {r["due_date"] or "-"}</p><p><b>Follow-up:</b> {r["follow_up"] or "-"}</p><hr><p>{(r["description"] or "No description").replace(chr(10),'<br>')}</p></div></section>')

@app.get('/task/{tid}/edit',response_class=HTMLResponse)
def edit(tid:int):
    c=db(); r=c.execute('select * from tasks where id=?',(tid,)).fetchone(); c.close(); return page(form_html(r)) if r else HTMLResponse('Not found',404)

@app.post('/task/{tid}/edit')
def edit_post(tid:int,title:str=Form(...),description:str=Form(''),category:str=Form(''),priority:str=Form('Medium'),status:str=Form('New'),assignee:str=Form(''),due_date:str=Form(''),follow_up:str=Form('')):
    c=db(); c.execute('update tasks set title=?,description=?,category=?,priority=?,status=?,assignee=?,due_date=?,follow_up=?,completed_at=case when ?="Completed" then CURRENT_TIMESTAMP else completed_at end where id=?',(title,description,category,priority,status,assignee,due_date,follow_up,status,tid)); c.commit(); c.close(); return RedirectResponse(f'/task/{tid}',303)
