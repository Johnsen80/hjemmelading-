"""
Gordon's Reloading Tool Database Importer
Read bullets, powders, primers from Gordon's SQLite database
"""

import sqlite3
import json
from typing import List, Dict

def read_gordon_database(db_path: str) -> Dict:
    """Read all data from Gordon's database"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📊 Tables in Gordon's database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    data = {}
    
    # Try to read projectiles (bullets)
    try:
        cursor.execute("SELECT * FROM projectile LIMIT 10")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        print(f"\n🎯 Projectile columns: {columns}")
        print(f"Found {len(rows)} projectiles (showing first 10)")
        
        data['projectiles'] = []
        for row in rows:
            proj = dict(zip(columns, row))
            data['projectiles'].append(proj)
            print(f"  - {proj.get('manufacturer', 'Unknown')} {proj.get('name', 'Unknown')} {proj.get('weight', 0)}gr")
    
    except Exception as e:
        print(f"❌ Error reading projectiles: {e}")
    
    # Try to read powders
    try:
        cursor.execute("SELECT * FROM powder LIMIT 10")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        print(f"\n💨 Powder columns: {columns}")
        print(f"Found {len(rows)} powders (showing first 10)")
        
        data['powders'] = []
        for row in rows:
            powder = dict(zip(columns, row))
            data['powders'].append(powder)
            print(f"  - {powder.get('manufacturer', 'Unknown')} {powder.get('name', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ Error reading powders: {e}")
    
    # Try to read primers
    try:
        cursor.execute("SELECT * FROM primer LIMIT 10")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        print(f"\n💥 Primer columns: {columns}")
        print(f"Found {len(rows)} primers")
        
        data['primers'] = []
        for row in rows:
            primer = dict(zip(columns, row))
            data['primers'].append(primer)
            print(f"  - {primer.get('manufacturer', 'Unknown')} {primer.get('name', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ Error reading primers: {e}")
    
    conn.close()
    
    return data


if __name__ == "__main__":
    import os
    
    db_path = "data/gordon_database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please copy Gordon's database to data/ folder")
    else:
        print(f"✅ Reading Gordon's database: {db_path}\n")
        data = read_gordon_database(db_path)
        
        # Save to JSON for inspection
        with open("data/gordon_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved data to gordon_data.json")
        print(f"📊 Total: {len(data.get('projectiles', []))} bullets, {len(data.get('powders', []))} powders, {len(data.get('primers', []))} primers")
