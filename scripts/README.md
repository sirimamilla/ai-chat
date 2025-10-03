# Scripts

Utility scripts for AI Chat development and deployment.

## setup_check.py

Validates your setup before running the application.

**Usage:**
```bash
python scripts/setup_check.py
```

**Checks:**
- ✓ Python version (3.9+)
- ✓ Required files (.env, config files)
- ✓ Dependencies installed
- ✓ Environment variables set
- ✓ Database connection

**Example Output:**
```
============================================================
AI Chat Setup Validation
============================================================

Python Version:
✓ Python 3.11.0

Required Files:
✓ Environment file: .env
✓ MCP configuration: config/mcp_servers.yaml

Dependency Check:
✓ LangChain
✓ LangGraph
✓ FastAPI
✓ SQLAlchemy
✓ Pydantic
✓ Click

Environment Variables:
✓ GOOGLE_CLOUD_PROJECT=my-project
✓ POSTGRES_HOST=localhost
✓ POSTGRES_DB=ai_chat
✓ POSTGRES_USER=postgres
✓ POSTGRES_PASSWORD=***

Database Connection:
✓ PostgreSQL connection successful

============================================================
✓ All checks passed! You're ready to go.

Next steps:
  1. Initialize database: python main.py init-database
  2. Start CLI: python main.py chat
  3. Start API: python main.py serve
```

## Future Scripts

Additional scripts that could be added:

- `deploy.sh`: Deployment automation
- `backup_db.py`: Database backup utility
- `migrate_db.py`: Database migration tool
- `benchmark.py`: Performance benchmarking
- `load_test.py`: Load testing script
