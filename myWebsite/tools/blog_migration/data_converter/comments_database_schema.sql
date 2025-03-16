-- Schema for comments database

-- Drop tables if they exist
DROP TABLE IF EXISTS comments;

-- Create comments table
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id TEXT UNIQUE, -- Original comment ID from Blogger
    post_id TEXT NOT NULL,  -- This will be the slug of the post
    parent_id INTEGER,      -- Reference to parent comment (NULL for top-level comments)
    author_name TEXT NOT NULL,
    author_email TEXT,      -- May be NULL for imported comments
    content TEXT NOT NULL,
    author_token TEXT,      -- Token to identify the author for editing/deleting
    created_at TEXT NOT NULL,
    last_edited_at TEXT,    -- Timestamp of last edit, if any
    status TEXT NOT NULL DEFAULT 'pending', -- 'approved', 'pending', 'spam'
    FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE
);

-- Create index on post_id for faster queries
CREATE INDEX idx_comments_post_id ON comments(post_id);

-- Create index on parent_id for faster hierarchical queries
CREATE INDEX idx_comments_parent_id ON comments(parent_id);

-- Add metadata table to track migration info
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Insert migration timestamp
INSERT INTO metadata (key, value) VALUES ('migration_date', CURRENT_TIMESTAMP);
