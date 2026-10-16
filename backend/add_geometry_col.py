from app.db import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME='counties' AND COLUMN_NAME='geometry'
    )
    ALTER TABLE counties ADD geometry NVARCHAR(MAX)
""")
conn.close()
print("✅ Geometry column ready")
