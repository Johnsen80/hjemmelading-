import json
import sqlite3

import requests  # type: ignore[import-untyped]


def sync_to_cloud(db_path, api_url):
    """
    Sync local SQLite database with a cloud-based API.

    :param db_path: Path to the SQLite database file.
    :param api_url: URL of the cloud API endpoint.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all data from the database
        cursor.execute("SELECT * FROM LoadRecipe")
        load_recipes = cursor.fetchall()

        # Convert data to JSON
        payload = json.dumps({"load_recipes": load_recipes})

        # Send data to the cloud API
        response = requests.post(
            api_url, data=payload, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print("Data synced successfully.")
        else:
            print(f"Failed to sync data. Status code: {response.status_code}")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

    except requests.RequestException as e:
        print(f"Request error: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # Example usage
    db_path = "../data/db.json"
    api_url = "https://example.com/api/sync"
    sync_to_cloud(db_path, api_url)
