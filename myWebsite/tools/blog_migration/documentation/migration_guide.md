# Blogger to Markdown Migration Tool

This tool migrates content from a Blogger XML export file to Markdown files for your Flask blog, while preserving comments in a SQLite database.

## Requirements

- Python 3.7+
- Blogger XML export file

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure your Blogger XML export file is available 

## Usage

Run the migration script:

```bash
python blogger_to_md.py path/to/your/blogger-export.xml
```

Optional arguments:
- `--output`: Specify a custom output directory for Markdown files (default: ../content/blog/posts)

## What This Does

1. Parses your Blogger XML export file
2. Converts blog posts to Markdown files with proper front matter
3. Extracts all comments and stores them in a SQLite database (`comments.sqlite`)
4. Maps comments to the correct posts using the post slugs

## Output

- Markdown files will be saved to `../content/blog/posts/` by default
- Comments will be stored in `comments.sqlite` in the current directory

## Next Steps

After running this migration:

1. Review the generated Markdown files and make any necessary adjustments
2. Integrate the comments SQLite database with your Flask application
3. Delete this migration folder once you've successfully integrated the content

## Comment Database Schema

The SQLite database contains a `comments` table with the following structure:

- `id`: Auto-incrementing primary key
- `comment_id`: Original comment ID from Blogger (unique)
- `post_id`: The post slug this comment belongs to
- `author_name`: Name of the comment author
- `author_email`: Email of the comment author (may be NULL for imported comments)
- `content`: The comment content
- `created_at`: Timestamp when the comment was created
- `status`: Comment status (approved, pending, spam)

## Integrating with Flask

To display comments in your Flask application, you'll need to:

1. Create a database connection function in your Flask app
2. Add routes for displaying and managing comments
3. Update your post template to show comments and a comment form
