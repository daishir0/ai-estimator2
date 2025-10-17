-- AI見積りシステム データベース初期化スクリプト

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS estimator;

-- タスクテーブル
CREATE TABLE IF NOT EXISTS estimator.tasks (
    id VARCHAR(36) PRIMARY KEY,
    excel_file_path VARCHAR(500) NOT NULL,
    system_requirements TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    result_file_path VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 成果物テーブル
CREATE TABLE IF NOT EXISTS estimator.deliverables (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL REFERENCES estimator.tasks(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT
);

-- 見積りテーブル
CREATE TABLE IF NOT EXISTS estimator.estimates (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL REFERENCES estimator.tasks(id) ON DELETE CASCADE,
    deliverable_name VARCHAR(200) NOT NULL,
    deliverable_description TEXT,
    person_days FLOAT NOT NULL,
    amount FLOAT NOT NULL,
    reasoning TEXT
);

-- Q&Aペアテーブル
CREATE TABLE IF NOT EXISTS estimator.qa_pairs (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL REFERENCES estimator.tasks(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT,
    "order" INTEGER NOT NULL
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_tasks_status ON estimator.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON estimator.tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_deliverables_task_id ON estimator.deliverables(task_id);
CREATE INDEX IF NOT EXISTS idx_estimates_task_id ON estimator.estimates(task_id);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_task_id ON estimator.qa_pairs(task_id);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_order ON estimator.qa_pairs(task_id, "order");
