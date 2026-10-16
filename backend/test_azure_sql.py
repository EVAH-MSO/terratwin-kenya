import pymssql

try:
    conn = pymssql.connect(
        server="terratwin-kenya-server-2026.database.windows.net",
        user="terratwin_admin@terratwin-kenya-server-2026",  # IMPORTANT: username@servername format
        password="Kutus@10304A!z",
        database="terratwin",
        port=1433,
    )
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print("✅ Connected to Azure SQL!")
    print(f"   Version: {row[0][:80]}...")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")