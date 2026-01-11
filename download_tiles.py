import os
import requests
from math import log, tan, pi, radians, floor, cos
import time
import random

def sec(x):
    return 1 / cos(x)

def lat_lon_to_tile(lat, lon, zoom):
    """Convert latitude/longitude to tile coordinates - FIXED VERSION"""
    lat_rad = radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
    return x, y

def download_delhi_tiles_fixed():
    """Download Delhi tiles with proper coordinate calculation and deeper zoom."""

    delhi_center_lat = 28.6139
    delhi_center_lon = 77.2090

    tile_servers = [
        "https://tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
        "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
        "https://cartodb-basemaps-b.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png"
    ]

    headers = {
        'User-Agent': 'Delhi-Nuclear-Simulator/1.0 (Educational)',
        'Accept': 'image/png,image/*',
    }

    tile_path = 'assets/tiles'

    zoom_levels = [10, 11, 12, 13, 14, 15, 16, 17]

    tile_radius = {
        10: 3,   

        11: 4,   

        12: 6,   

        13: 8,   

        14: 12,  

        15: 20,  

        16: 35,  

        17: 60   

    }

    total_downloaded = 0
    total_attempted = 0

    print("🏙 DELHI NUCLEAR FALLOUT SIMULATOR - TILE DOWNLOADER")
    print("=" * 60)
    print(f"📍 Center: {delhi_center_lat}, {delhi_center_lon}")
    print(f"💾 Saving to: {tile_path}")
    print(f"📡 Zoom Levels to Download: {zoom_levels}")
    print()

    for zoom in zoom_levels:
        print(f"🔍 ZOOM LEVEL {zoom}")
        print("-" * 30)

        center_x, center_y = lat_lon_to_tile(delhi_center_lat, delhi_center_lon, zoom)
        radius = tile_radius[zoom]

        x_min = center_x - radius
        x_max = center_x + radius
        y_min = center_y - radius  
        y_max = center_y + radius

        max_tile = (2 ** zoom) - 1
        x_min = max(0, x_min)
        x_max = min(max_tile, x_max)
        y_min = max(0, y_min)
        y_max = min(max_tile, y_max)

        tiles_needed = (x_max - x_min + 1) * (y_max - y_min + 1)
        print(f"📊 Center tile: {center_x}, {center_y}")
        print(f"📦 Range: X({x_min}-{x_max}) Y({y_min}-{y_max})")
        print(f"🎯 Tiles to download: {tiles_needed}")

        zoom_downloaded = 0
        zoom_attempted = 0

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                zoom_attempted += 1
                total_attempted += 1

                tile_dir = os.path.join(tile_path, str(zoom), str(x))
                tile_file = os.path.join(tile_dir, f"{y}.png")

                if os.path.exists(tile_file):
                    try:
                        with open(tile_file, 'rb') as f:
                            if f.read(4) == b'\x89PNG':
                                continue
                    except:
                        pass

                os.makedirs(tile_dir, exist_ok=True)

                success = False
                for server in tile_servers:
                    if success:
                        break

                    url = server.format(z=zoom, x=x, y=y)

                    try:
                        time.sleep(random.uniform(0.1, 0.4))

                        response = requests.get(url, headers=headers, timeout=10)

                        if response.status_code == 200:
                            content = response.content
                            if len(content) > 100 and content.startswith(b'\x89PNG'):
                                with open(tile_file, 'wb') as f:
                                    f.write(content)

                                zoom_downloaded += 1
                                total_downloaded += 1
                                success = True

                                if total_downloaded % 20 == 0:
                                    progress = (zoom_attempted / tiles_needed) * 100
                                    print(f"  📥 {zoom_downloaded}/{tiles_needed} ({progress:.1f}%) - Total: {total_downloaded}")

                                break

                    except:
                        continue

                if not success:
                    print(f"  ❌ Failed: {zoom}/{x}/{y}")

        success_rate = (zoom_downloaded / tiles_needed) * 100 if tiles_needed > 0 else 0
        print(f"✅ Zoom {zoom} Complete: {zoom_downloaded}/{tiles_needed} tiles ({success_rate:.1f}%)")
        print()

    print("🎉 DOWNLOAD COMPLETE!")
    print("=" * 40)
    print(f"📊 Total tiles downloaded: {total_downloaded}")
    print(f"📈 Success rate: {(total_downloaded/total_attempted)*100:.1f}%")

    if total_downloaded > 50:
        print("✅ SUCCESS! Your Delhi map should now work offline!")
        print("🗺  Try running your Nuclear Fallout Simulator now.")
    else:
        print("⚠  Low download count. Check your internet connection.")

    return total_downloaded

if __name__== '__main__':
    print("Starting Delhi tile download...")
    try:
        downloaded = download_delhi_tiles_fixed()
        if downloaded > 0:
            print(f"\n🚀 Ready to use! {downloaded} Delhi tiles downloaded.")
        else:
            print("\n❌ No tiles downloaded. Please check your internet connection.")
    except KeyboardInterrupt:
        print("\n⏹ Download stopped by user.")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        print("🔧 Try running the script again.")