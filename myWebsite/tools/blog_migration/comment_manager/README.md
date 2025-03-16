# Comment Management Tools

This directory contains tools for managing comment relationships in the migrated blog.

## Tools Included

### 1. Comment Relationship Manager (`comment_relationship_manager.py`)

An interactive tool for manually managing parent-child relationships between comments.

**Features:**
- View all comments for each post
- Set parent-child relationships manually
- Clear parent-child relationships
- View the comment thread structure

**Usage:**
```bash
python comment_relationship_manager.py [path/to/comments.sqlite]
```

### 2. Comment Hierarchy Fixer (`comment_hierarchy_fixer.py`) 

A tool that attempts to automatically detect and repair parent-child relationships between comments.

**Features:**
- Interactive and automatic modes
- Detects potential replies based on content analysis
- Fixes broken hierarchies
- Provides visualizations of comment threads

**Usage:**
```bash
python comment_hierarchy_fixer.py --mode [interactive|auto|manual] --db [path/to/database]
```

## Workflow

1. First run the hierarchy fixer to automatically detect relationships
2. Use the relationship manager to manually fix any remaining issues
3. Verify the comment display on your blog

## Notes

- These tools modify the comments database directly, so consider making a backup first
- The automatic detection isn't perfect and may require manual verification
