import os
import requests
from math import log, tan, pi, radians, floor, cos, ceil, atan, exp, sin, atan2, sqrt
import time
import random
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.properties import BoundedNumericProperty, NumericProperty
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock

def sec(x):
    return 1 / cos(x)

def sinh(x):
    """Hyperbolic sine function"""
    return (exp(x) - exp(-x)) / 2.0

def lat_lon_to_tile(lat, lon, zoom):
    """Convert latitude/longitude to tile coordinates"""
    lat_rad = radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - log(tan(lat_rad) + sec(lat_rad)) / pi) / 2.0 * n)
    return x, y

def tile_to_lat_lon(x, y, zoom):
    """Convert tile coordinates to latitude/longitude"""
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * y / n)))
    lat = lat_rad * 180.0 / pi
    return lat, lon

def download_tile(x, y, zoom, tiles_folder='tiles'):
    """Download a single tile from OpenStreetMap"""
    if not os.path.exists(tiles_folder):
        os.makedirs(tiles_folder)

    zoom_folder = os.path.join(tiles_folder, str(zoom))
    if not os.path.exists(zoom_folder):
        os.makedirs(zoom_folder)

    x_folder = os.path.join(zoom_folder, str(x))
    if not os.path.exists(x_folder):
        os.makedirs(x_folder)

    tile_path = os.path.join(x_folder, f"{y}.png")

    if os.path.exists(tile_path):
        return tile_path

    try:
        url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
        headers = {'User-Agent': 'Nuclear Fallout Simulator/1.0 (Educational Use)'}
        time.sleep(0.1 + random.uniform(0, 0.1))

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        with open(tile_path, 'wb') as f:
            f.write(response.content)

        print(f"Downloaded tile {zoom}/{x}/{y}")
        return tile_path
    except Exception as e:
        print(f"Failed to download tile {zoom}/{x}/{y}: {e}")
        return None

class OfflineMap(Widget):
    """Enhanced map widget with fixed coordinate conversion"""

    lat = NumericProperty(28.6139)
    lon = NumericProperty(77.2090)
    zoom = BoundedNumericProperty(10, min=1, max=18)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.tiles_path = 'tiles'
        self.tile_size = 256

        self.delhi_bounds = {
            'north': 28.8833,
            'south': 28.4044,
            'east': 77.3489,
            'west': 76.9833
        }

        self.touch_start_pos = None
        self.initial_lat = self.lat
        self.initial_lon = self.lon

        self.bind(pos=self.redraw_map, size=self.redraw_map)
        self.bind(lat=self.redraw_map, lon=self.redraw_map, zoom=self.redraw_map)

        Clock.schedule_once(self.redraw_map, 0.1)

    def center_on(self, lat, lon):
        """Center the map on specific coordinates"""
        print(f"Centering map on: {lat}, {lon}")
        self.lat = lat
        self.lon = lon

        if not self.is_in_delhi(lat, lon):
            self.zoom = max(8, self.zoom - 2)

    def is_in_delhi(self, lat, lon):
        """Check if coordinates are within Delhi bounds"""
        return (self.delhi_bounds['south'] <= lat <= self.delhi_bounds['north'] and
                self.delhi_bounds['west'] <= lon <= self.delhi_bounds['east'])

    def lat_lon_to_xy(self, lat, lon):
        """Convert lat/lon to widget pixel coordinates - FIXED VERSION"""
        n = 2.0 ** self.zoom

        center_x = (self.lon + 180.0) / 360.0 * n
        center_y = (1.0 - log(tan(radians(self.lat)) + sec(radians(self.lat))) / pi) / 2.0 * n

        target_x = (lon + 180.0) / 360.0 * n
        target_y = (1.0 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2.0 * n

        pixel_x = self.center_x + (target_x - center_x) * self.tile_size
        pixel_y = self.center_y + (target_y - center_y) * self.tile_size

        return pixel_x, pixel_y

    def xy_to_lat_lon(self, x, y):
        """Convert widget pixel coordinates to lat/lon"""
        pixel_offset_x = x - self.center_x
        pixel_offset_y = y - self.center_y

        tile_offset_x = pixel_offset_x / self.tile_size
        tile_offset_y = pixel_offset_y / self.tile_size

        n = 2.0 ** self.zoom
        center_x = (self.lon + 180.0) / 360.0 * n
        center_y = (1.0 - log(tan(radians(self.lat)) + sec(radians(self.lat))) / pi) / 2.0 * n

        target_x = center_x + tile_offset_x
        target_y = center_y + tile_offset_y

        lon = target_x / n * 360.0 - 180.0
        lat_rad = atan(sinh(pi * (1 - 2 * target_y / n)))
        lat = lat_rad * 180.0 / pi

        return lat, lon

    def get_visible_tiles(self):
        """Calculate which tiles need to be displayed"""
        if self.width <= 0 or self.height <= 0:
            return []

        center_tile_x, center_tile_y = lat_lon_to_tile(self.lat, self.lon, self.zoom)

        tiles_x = ceil(self.width / self.tile_size) + 2
        tiles_y = ceil(self.height / self.tile_size) + 2

        min_tile_x = int(center_tile_x - tiles_x // 2)
        max_tile_x = int(center_tile_x + tiles_x // 2)
        min_tile_y = int(center_tile_y - tiles_y // 2)
        max_tile_y = int(center_tile_y + tiles_y // 2)

        tiles = []
        max_tile_coord = 2 ** self.zoom

        for tile_x in range(min_tile_x, max_tile_x + 1):
            for tile_y in range(min_tile_y, max_tile_y + 1):
                wrapped_x = tile_x % max_tile_coord
                if 0 <= tile_y < max_tile_coord:
                    tiles.append((wrapped_x, tile_y, tile_x, tile_y))

        return tiles

    def redraw_map(self, *args):
        """Redraw the map with current tiles"""
        self.canvas.clear()

        if self.width <= 0 or self.height <= 0:
            return

        visible_tiles = self.get_visible_tiles()
        center_tile_x, center_tile_y = lat_lon_to_tile(self.lat, self.lon, self.zoom)

        with self.canvas:
            Color(0.9, 0.9, 0.9, 1)
            Rectangle(pos=self.pos, size=self.size)

            for wrapped_x, tile_y, original_x, original_y in visible_tiles:
                tile_offset_x = original_x - center_tile_x
                tile_offset_y = original_y - center_tile_y

                tile_pos_x = self.center_x + (tile_offset_x * self.tile_size) - self.tile_size // 2
                tile_pos_y = self.center_y - (tile_offset_y * self.tile_size) - self.tile_size // 2

                tile_path = self.get_tile_image(wrapped_x, tile_y, self.zoom)

                if tile_path and os.path.exists(tile_path):
                    try:
                        texture = CoreImage(tile_path).texture
                        Color(1, 1, 1, 1)
                        Rectangle(texture=texture, pos=(tile_pos_x, tile_pos_y), 
                                size=(self.tile_size, self.tile_size))
                    except Exception as e:
                        Color(0.8, 0.8, 0.8, 1)
                        Rectangle(pos=(tile_pos_x, tile_pos_y), 
                                size=(self.tile_size, self.tile_size))
                else:
                    Color(0.7, 0.7, 0.7, 1)
                    Rectangle(pos=(tile_pos_x, tile_pos_y), 
                            size=(self.tile_size, self.tile_size))

                    Clock.schedule_once(
                        lambda dt, x=wrapped_x, y=tile_y, z=self.zoom: 
                        self.download_tile_async(x, y, z), 0.1
                    )

    def get_tile_image(self, x, y, zoom):
        """Get path to tile image file"""
        tile_path = os.path.join(self.tiles_path, str(zoom), str(x), f"{y}.png")
        return tile_path if os.path.exists(tile_path) else None

    def download_tile_async(self, x, y, zoom):
        """Download tile asynchronously and refresh map"""
        try:
            tile_path = download_tile(x, y, zoom, self.tiles_path)
            if tile_path:
                Clock.schedule_once(self.redraw_map, 0.1)
        except Exception as e:
            print(f"Async tile download failed: {e}")

    def on_touch_down(self, touch):
        """Handle touch start for panning"""
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.touch_start_pos = touch.pos
            self.initial_lat = self.lat
            self.initial_lon = self.lon
            return True
        return False

    def on_touch_move(self, touch):
        """Handle touch move for panning"""
        if touch.grab_current is self and self.touch_start_pos:
            dx = touch.pos[0] - self.touch_start_pos[0]
            dy = touch.pos[1] - self.touch_start_pos[1]

            lat_per_pixel = 180.0 / (2 ** self.zoom * self.tile_size)
            lon_per_pixel = 360.0 / (2 ** self.zoom * self.tile_size)

            self.lat = self.initial_lat + (dy * lat_per_pixel)
            self.lon = self.initial_lon - (dx * lon_per_pixel)

            self.lat = max(-85, min(85, self.lat))
            self.lon = max(-180, min(180, self.lon))

            return True
        return False

    def on_touch_up(self, touch):
        """Handle touch end"""
        if touch.grab_current is self:
            touch.ungrab(self)
            self.touch_start_pos = None
            return True
        return False

    def zoom_in(self, center_pos=None):
        """Zoom in on the map"""
        if self.zoom < 18:
            if center_pos:
                lat, lon = self.xy_to_lat_lon(*center_pos)
                self.zoom += 1
                self.center_on(lat, lon)
            else:
                self.zoom += 1

    def zoom_out(self, center_pos=None):
        """Zoom out on the map"""
        if self.zoom > 1:
            if center_pos:
                lat, lon = self.xy_to_lat_lon(*center_pos)
                self.zoom -= 1
                self.center_on(lat, lon)
            else:
                self.zoom -= 1

def preload_delhi_tiles():
    """Pre-download key Delhi tiles"""
    delhi_center = (28.6139, 77.2090)
    zoom_levels = [9, 10, 11]

    print("Pre-loading Delhi map tiles...")
    for zoom in zoom_levels:
        center_x, center_y = lat_lon_to_tile(delhi_center[0], delhi_center[1], zoom)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                try:
                    download_tile(center_x + dx, center_y + dy, zoom)
                except Exception as e:
                    print(f"Preload failed: {e}")