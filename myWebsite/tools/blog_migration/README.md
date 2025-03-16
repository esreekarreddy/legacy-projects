# Blogger to Flask Blog Migration Tools

This directory contains a complete toolkit for migrating from Blogger to a custom Flask-based blog platform.

## Directory Structure

- **data_converter/** - Tools for converting Blogger XML to Markdown and SQLite
- **comment_manager/** - Tools for managing comment hierarchies and relationships
- **documentation/** - Detailed documentation of the migration process

## Migration Process Overview

1. **Export from Blogger**
   - Download the XML export file from Blogger settings

2. **Convert Posts and Comments**
   - Use `data_converter/blogger_xml_to_markdown.py` to convert XML to Markdown files
   - Comments are automatically extracted to a SQLite database

3. **Fix Comment Relationships**
   - Use `comment_manager/comment_hierarchy_fixer.py` to detect parent-child relationships
   - Use `comment_manager/comment_relationship_manager.py` to manually correct relationships

4. **Integrate with Flask Application**
   - Move the SQLite database to the root directory of your Flask application
   - Ensure the Flask app is configured to use the database for comments

## Notes for Future Reference

- The most challenging part of the migration was preserving comment hierarchies
- The data converter attempts to automatically detect parent-child relationships, but manual review is recommended
- These tools were built specifically for the Blogger XML format as of 2023

## Contributors

- Sreekar Reddy
