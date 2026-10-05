# Everest IT Task Manager — MVP

## Run with Docker

```bash
docker compose up -d --build
```

Open: `http://SERVER-IP:8000`

Data is stored in `./data/tasks.db` and survives container restarts.

## Run without Docker

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Included
- Dashboard
- Task creation/editing
- Priority and status
- Categories
- Assignee and due date
- Follow-up date
- Search/filter
- Responsive/mobile layout

## Next production phase
- Login / Microsoft Entra ID
- PostgreSQL
- Role-based access
- Recurring tasks
- Email/Teams notifications
- Attachments
- Audit log
- Monthly PDF/Excel report
- Backup/restore
