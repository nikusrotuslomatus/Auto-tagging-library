from database import Database

class TagManager:
    def __init__(self, db: Database):
        self.db = db

    def create_tag(self, name: str, tag_type: str) -> int:
        """
        Create a new tag. tag_type must be one of: 'boolean', 'numeric', or 'string'.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tags (name, type) VALUES (?, ?)
        """, (name, tag_type))
        tag_id = cursor.lastrowid
        conn.commit()
        self.log_action(f"Created tag: {name} (ID={tag_id}, type={tag_type})")
        return tag_id

    def delete_tag(self, tag_id: int):
        """
        Delete a tag. Cascades to file_tags.
        """
        conn = self.db.get_connection()
        with conn:
            conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            self.log_action(f"Deleted tag with ID={tag_id}")

    def assign_tag_to_file(self, file_id: int, tag_id: int, value: str = None):
        """
        Assign a tag to a file. Optionally set a value (e.g., numeric or string).
        """
        conn = self.db.get_connection()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_tags (file_id, tag_id, value)
                VALUES (?, ?, ?)
            """, (file_id, tag_id, value))
            self.log_action(f"Assigned tag (ID={tag_id}) to file (ID={file_id}), value={value}")

    def remove_tag_from_file(self, file_id: int, tag_id: int):
        """
        Remove a tag assignment from a file.
        """
        conn = self.db.get_connection()
        with conn:
            conn.execute("""
                DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?
            """, (file_id, tag_id))
            self.log_action(f"Removed tag (ID={tag_id}) from file (ID={file_id})")

    def get_tags_for_file(self, file_id: int):
        """
        Get all tags assigned to a given file.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tags.id, tags.name, tags.type, file_tags.value
            FROM tags
            JOIN file_tags ON tags.id = file_tags.tag_id
            WHERE file_tags.file_id = ?
        """, (file_id,))
        return cursor.fetchall()

    def log_action(self, action: str):
        """
        Log tagging-related actions.
        """
        conn = self.db.get_connection()
        conn.execute("INSERT INTO logs (action) VALUES (?)", (action,))
        conn.commit()

    def get_all_tags(self):
        """
        Returns a list of (id, name, type) for all tags.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type FROM tags ORDER BY name ASC")
        return cursor.fetchall()

    def get_all_tag_names(self):
        """
        Returns a list of all distinct tag names in the 'tags' table.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM tags ORDER BY name ASC")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
