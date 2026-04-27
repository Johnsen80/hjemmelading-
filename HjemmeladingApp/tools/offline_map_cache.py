import os

import requests


class OfflineMapCache:
    def __init__(self, cache_dir="cache/maps"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_tile(self, url, tile_name):
        """
        Fetch a map tile and cache it locally.

        :param url: URL of the map tile.
        :param tile_name: Name to save the tile as.
        """
        tile_path = os.path.join(self.cache_dir, tile_name)
        if os.path.exists(tile_path):
            print(f"Tile {tile_name} loaded from cache.")
            return tile_path

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(tile_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Tile {tile_name} cached.")
            return tile_path
        else:
            print(f"Failed to fetch tile: {response.status_code}")
            return None


if __name__ == "__main__":
    # Example usage
    cache = OfflineMapCache()
    tile_url = "https://tile.openstreetmap.org/0/0/0.png"
    cache.fetch_tile(tile_url, "0_0_0.png")
