#!/usr/bin/env python
"""Setup validation script for AI Chat."""

import os
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_mark(passed: bool) -> str:
    """Return colored check mark or X."""
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 9
    status = check_mark(passed)
    print(f"{status} Python {version.major}.{version.minor}.{version.micro}")
    return passed


def check_file_exists(filepath: str, description: str):
    """Check if a file exists."""
    passed = Path(filepath).exists()
    status = check_mark(passed)
    print(f"{status} {description}: {filepath}")
    return passed


def check_env_file():
    """Check if .env file exists."""
    return check_file_exists(".env", "Environment file")


def check_config_file():
    """Check if MCP config exists."""
    return check_file_exists("config/mcp_servers.yaml", "MCP configuration")


def check_dependencies():
    """Check if key dependencies are installed."""
    dependencies = [
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("click", "Click"),
    ]

    all_passed = True
    print("\nDependency Check:")

    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"{check_mark(True)} {display_name}")
        except ImportError:
            print(f"{check_mark(False)} {display_name}")
            all_passed = False

    return all_passed


def check_env_variables():
    """Check if required environment variables are set."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print(f"{YELLOW}Note: python-dotenv not installed, skipping .env loading{RESET}")

    required_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]

    all_set = True
    print("\nEnvironment Variables:")

    for var in required_vars:
        value = os.getenv(var)
        passed = value is not None and value != ""
        status = check_mark(passed)
        if passed:
            print(f"{status} {var}={value[:20]}..." if len(value) > 20 else f"{status} {var}={value}")
        else:
            print(f"{status} {var} (not set)")
        all_set = all_set and passed

    return all_set


def check_database_connection():
    """Check if can connect to PostgreSQL."""
    print("\nDatabase Connection:")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.ai_chat.config import settings
        import psycopg2

        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
        conn.close()
        print(f"{check_mark(True)} PostgreSQL connection successful")
        return True
    except ImportError:
        print(f"{check_mark(False)} psycopg2 not installed")
        return False
    except Exception as e:
        print(f"{check_mark(False)} Connection failed: {str(e)}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("AI Chat Setup Validation")
    print("=" * 60)

    print("\nPython Version:")
    checks = [check_python_version()]

    print("\nRequired Files:")
    checks.append(check_env_file())
    checks.append(check_config_file())

    checks.append(check_dependencies())
    checks.append(check_env_variables())
    checks.append(check_database_connection())

    print("\n" + "=" * 60)
    if all(checks):
        print(f"{GREEN}✓ All checks passed! You're ready to go.{RESET}")
        print("\nNext steps:")
        print("  1. Initialize database: python main.py init-database")
        print("  2. Start CLI: python main.py chat")
        print("  3. Start API: python main.py serve")
        return 0
    else:
        print(f"{RED}✗ Some checks failed. Please review the issues above.{RESET}")
        print("\nTroubleshooting:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Create .env file: cp .env.example .env")
        print("  3. Configure .env with your settings")
        print("  4. Ensure PostgreSQL is running")
        return 1


if __name__ == "__main__":
    sys.exit(main())
