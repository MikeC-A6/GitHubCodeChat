-- Create repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    description TEXT,
    files JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    branch TEXT NOT NULL DEFAULT 'main',
    path TEXT NOT NULL DEFAULT '',
    processed_at TIMESTAMP,
    vectorized BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS repositories_status_idx ON repositories(status);
CREATE INDEX IF NOT EXISTS repositories_vectorized_idx ON repositories(vectorized); 