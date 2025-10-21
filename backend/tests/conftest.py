"""pytest shared fixtures"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, MagicMock
import json

from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings

# Test database - use file-based SQLite for test isolation
TEST_DB_FILE = "/tmp/test_estimator.db"

# Remove old test database if it exists
if os.path.exists(TEST_DB_FILE):
    os.remove(TEST_DB_FILE)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Test database session"""
    # Enable foreign keys for SQLite
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables for next test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Test FastAPI client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai_response():
    """Mock data for OpenAI API responses"""
    return {
        "questions": {
            "questions": ["Question 1", "Question 2", "Question 3"]
        },
        "estimate": {
            "estimated_effort_days": 5.0,
            "breakdown": "Requirements: 2 days\nDesign: 3 days",
            "rationale": "Estimated based on system scope"
        },
        "chat_adjustment": {
            "suggestions": [
                {
                    "title": "Suggestion 1",
                    "description": "Description 1",
                    "impact": "Impact 1"
                }
            ]
        }
    }


@pytest.fixture
def mock_openai(monkeypatch, mock_openai_response):
    """Mock for OpenAI API"""

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message_content):
            self.message = MockMessage(message_content)

    class MockChatCompletion:
        def __init__(self, response_data):
            self.choices = [MockChoice(json.dumps(response_data))]

    class MockCompletions:
        def __init__(self, response_data):
            self.response_data = response_data

        def create(self, model=None, messages=None, temperature=None, max_tokens=None, timeout=None, **kwargs):
            # Return appropriate response based on prompt content
            last_message = messages[-1]["content"] if messages else ""

            if "質問" in last_message or "question" in last_message.lower():
                return MockChatCompletion(mock_openai_response["questions"])
            elif "見積" in last_message or "estimate" in last_message.lower():
                return MockChatCompletion(mock_openai_response["estimate"])
            elif "調整" in last_message or "adjust" in last_message.lower():
                return MockChatCompletion(mock_openai_response["chat_adjustment"])
            else:
                return MockChatCompletion(mock_openai_response["questions"])

    class MockChat:
        def __init__(self, response_data):
            self.completions = MockCompletions(response_data)

    class MockOpenAI:
        def __init__(self, api_key=None, timeout=None, **kwargs):
            self.chat = MockChat(mock_openai_response)
            self.timeout = timeout

    # Mock openai.OpenAI
    import sys
    if 'openai' not in sys.modules:
        sys.modules['openai'] = MagicMock()

    def mock_openai_constructor(api_key=None, timeout=None, **kwargs):
        return MockOpenAI(api_key=api_key, timeout=timeout, **kwargs)

    monkeypatch.setattr("openai.OpenAI", mock_openai_constructor)

    return MockOpenAI


@pytest.fixture
def sample_excel_file(tmp_path):
    """Sample Excel file for testing"""
    file_path = tmp_path / "test_sample.xlsx"
    df = pd.DataFrame({
        "成果物名称": ["要件定義書", "基本設計書", "詳細設計書"],
        "説明": [
            "システム全体の要件を定義する文書",
            "システムの基本設計を記述する文書",
            "システムの詳細設計を記述する文書"
        ]
    })
    df.to_excel(file_path, index=False, engine='openpyxl')
    return str(file_path)


@pytest.fixture
def sample_csv_file(tmp_path):
    """Sample CSV file for testing"""
    file_path = tmp_path / "test_sample.csv"
    df = pd.DataFrame({
        "成果物名称": ["要件定義書", "基本設計書"],
        "説明": [
            "システム全体の要件を定義する文書",
            "システムの基本設計を記述する文書"
        ]
    })
    df.to_csv(file_path, index=False, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def sample_deliverables():
    """Sample deliverable data for testing"""
    return [
        {"name": "要件定義書", "description": "システム全体の要件を定義する文書"},
        {"name": "基本設計書", "description": "システムの基本設計を記述する文書"},
        {"name": "詳細設計書", "description": "システムの詳細設計を記述する文書"}
    ]


@pytest.fixture
def sample_qa_pairs():
    """Sample Q&A pair data for testing"""
    return [
        {"question": "想定ユーザー数は？", "answer": "100名程度"},
        {"question": "開発期間は？", "answer": "3ヶ月"},
        {"question": "使用技術は？", "answer": "Python, FastAPI"}
    ]


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "id": "test-task-123",
        "status": "pending",
        "system_requirements": "Webベースの見積りシステム"
    }


@pytest.fixture
def temp_upload_dir(tmp_path, monkeypatch):
    """Temporary upload directory for testing"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))
    return str(upload_dir)


@pytest.fixture
def mock_language_ja(monkeypatch):
    """Set language to Japanese"""
    monkeypatch.setattr(settings, "LANGUAGE", "ja")
    # Reinitialize i18n to reload translations with new language
    from app.core import i18n
    monkeypatch.setattr(i18n, "i18n", i18n.I18n("ja"))
    return "ja"


@pytest.fixture
def mock_language_en(monkeypatch):
    """Set language to English"""
    monkeypatch.setattr(settings, "LANGUAGE", "en")
    # Reinitialize i18n to reload translations with new language
    from app.core import i18n
    monkeypatch.setattr(i18n, "i18n", i18n.I18n("en"))
    return "en"
