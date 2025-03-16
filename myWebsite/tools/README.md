# Blog Migration and Management Tools

This directory contains various tools developed for migrating content from Blogger to this Flask-based blog platform and managing the imported content.

## Directory Structure

- **blog_migration/** - Tools for migrating from Blogger XML export
  - **data_converter/** - XML to Markdown conversion utilities
  - **comment_manager/** - Comment hierarchy and relationship management tools
  - **documentation/** - Migration process documentation and guides

## Usage

Each tool directory contains its own README with specific instructions. Generally:

1. Migration process starts with converting Blogger XML to Markdown and SQLite
2. Comment hierarchies can be managed with the comment management tools
3. Once migration is complete, the blog should use the SQLite database for comments

## Development History

These tools were developed in 2023 to migrate blog content from Blogger while preserving comments and their threaded structure. The primary challenge was maintaining parent-child relationships between comments during migration.

## License

All tools are for personal use only.
