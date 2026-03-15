-- IU Comments Database Schema
-- 初始化数据库表结构

CREATE TABLE IF NOT EXISTS iu_comments (
    id SERIAL PRIMARY KEY,
    comment_text TEXT NOT NULL,
    author VARCHAR(255),
    created_at TIMESTAMP,
    page_url VARCHAR(500),
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引以提高查询效率
CREATE INDEX IF NOT EXISTS idx_iu_comments_author ON iu_comments(author);
CREATE INDEX IF NOT EXISTS idx_iu_comments_created_at ON iu_comments(created_at);
CREATE INDEX IF NOT EXISTS idx_iu_comments_fetched_at ON iu_comments(fetched_at);

-- 查看表结构
-- \d iu_comments

-- 查询示例:
-- SELECT * FROM iu_comments ORDER BY created_at DESC LIMIT 50;
-- SELECT author, COUNT(*) as count FROM iu_comments GROUP BY author ORDER BY count DESC;
-- SELECT DATE(created_at) as date, COUNT(*) as count FROM iu_comments GROUP BY date ORDER BY date DESC;
