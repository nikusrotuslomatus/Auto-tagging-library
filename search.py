from database import Database

class SearchEngine:
    def __init__(self, db: Database):
        self.db = db

    def search_by_filename(self, query: str):
        """
        Search for files whose filename contains the given query (basic LIKE search).
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        query_str = f"%{query}%"
        cursor.execute("""
            SELECT * FROM files
            WHERE file_path LIKE ?
        """, (query_str,))
        return cursor.fetchall()

    def search_by_tag_name(self, tag_name: str):
        """
        Search files by a specific tag name.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*
            FROM files f
            JOIN file_tags ft ON f.id = ft.file_id
            JOIN tags t ON t.id = ft.tag_id
            WHERE t.name = ?
        """, (tag_name,))
        return cursor.fetchall()

    def search_by_tag_value(self, tag_name: str, value: str):
        """
        Search files by a tag name and a specific value.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*
            FROM files f
            JOIN file_tags ft ON f.id = ft.file_id
            JOIN tags t ON t.id = ft.tag_id
            WHERE t.name = ? AND ft.value = ?
        """, (tag_name, value))
        return cursor.fetchall()

    def search_all(self, query: str):
        """
        Search for files matching 'query' in:
          - File path
          - File name (the base filename)
          - File metadata
          - Tag name
          - Tag value

        Returns a list of (file_id, file_name, file_path, metadata).
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        pattern = f"%{query}%"
        # Use DISTINCT to avoid duplicates if multiple tags match.
        cursor.execute("""
            SELECT DISTINCT f.id, f.name, f.file_path, f.metadata
            FROM files f
            LEFT JOIN file_tags ft ON f.id = ft.file_id
            LEFT JOIN tags t ON t.id = ft.tag_id
            WHERE f.file_path LIKE ?
               OR f.name LIKE ?
               OR f.metadata LIKE ?
               OR t.name LIKE ?
               OR ft.value LIKE ?
        """, (pattern, pattern, pattern, pattern, pattern))
        return cursor.fetchall()

    # (You may keep or remove other specialized searches like search_by_filename, etc.)
