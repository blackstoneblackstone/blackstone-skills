---
name: yuque
description: Yuque (语雀) document integration for reading, writing, and managing documents
version: 1.0.0
disabled: true
---

# Yuque (语雀) Skill

This skill provides integration with Yuque (语雀) document platform, allowing you to read, write, and manage documents.

## Available Tools

### Read Document
Read a Yuque document by URL or slug.

**Usage:**
```bash
curl -s "https://www.yuque.com/api/v2/repos/{namespace}/docs/{slug}" \
  -H "X-Auth-Token: {token}"
```

### List Documents
List documents in a Yuque repository.

**Usage:**
```bash
curl -s "https://www.yuque.com/api/v2/repos/{namespace}/docs" \
  -H "X-Auth-Token: {token}"
```

### Search Documents
Search for documents in Yuque.

**Usage:**
Use Yuque web interface or API with search parameters.

## Configuration

To use this skill, you need:
1. Yuque account
2. API Token (from Yuque Settings -> Tokens)

Set the token as environment variable:
```bash
export YUQUE_TOKEN=your_token_here
```

## API Reference

Yuque API documentation: https://www.yuque.com/yuque/developer/api

## Examples

### Read a document
```
读取语雀文档 https://www.yuque.com/username/repo/slug
```

### List repository documents
```
列出语雀知识库 username/repo 的文档
```
