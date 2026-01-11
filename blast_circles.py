'''from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
import math

class BlastCirclesWidget(Widget):
    """Draws blast effect circles on map"""

    def __init__(self, yield_kt, center_lat_lon, offline_map_widget, **kwargs):
        super().__init__(**kwargs)
        self.yield_kt = yield_kt
        self.center_lat_lon = center_lat_lon
        self.offline_map_widget = offline_map_widget

        self.offline_map_widget.bind(lat=self.redraw, lon=self.redraw, zoom=self.redraw)
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0.1)

    def calculate_blast_radii_km(self):
        """Calculate blast radii in km - scales with yield"""
        Y_MT = self.yield_kt / 1000.0

        return {
            'fireball': 0.15 * (Y_MT ** 0.4),
            'blast_20psi': 0.46 * (Y_MT ** 0.33),
            'blast_5psi': 0.99 * (Y_MT ** 0.40),
            'radiation_500rem': 1.25 * (Y_MT ** 0.19),
            'thermal_3rd': 1.41 * (Y_MT ** 0.41)
        }

    def km_to_pixels(self, km_distance):
        """Convert km to screen pixels - FIXED"""

        lat = self.center_lat_lon[0]

        meters_per_pixel = (156543.03 * abs(math.cos(math.radians(lat)))) / (2 ** self.offline_map_widget.zoom)

        pixels = (km_distance * 1000) / meters_per_pixel

        return pixels

    def redraw(self, *args):
        """Draw all blast circles"""
        self.canvas.clear()

        center_x, center_y = self.offline_map_widget.lat_lon_to_xy(
            self.center_lat_lon[0], self.center_lat_lon[1]
        )

        radii = self.calculate_blast_radii_km()

        circles = [
            ('fireball', 1, 1, 0, 0.7),
            ('blast_20psi', 1, 0, 0, 0.5),
            ('blast_5psi', 0.5, 0.5, 0.5, 0.4),
            ('radiation_500rem', 0, 1, 0, 0.4),
            ('thermal_3rd', 1, 0.5, 0, 0.4)
        ]

        with self.canvas:
            for key, r, g, b, a in reversed(circles):
                radius_km = radii[key]
                radius_px = self.km_to_pixels(radius_km)

                Color(r, g, b, a)
                Ellipse(pos=(center_x - radius_px, center_y - radius_px),
                       size=(radius_px * 2, radius_px * 2))

                Color(r, g, b, 0.9)
                Line(circle=(center_x, center_y, radius_px), width=1.5)

class MapClickHandler(Widget):
    """Handles map clicks - only updates dropdown selection to nearest location"""

    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance

    def find_nearest_location(self, lat, lon):
        """Find nearest Delhi location from dropdown list"""
        from delhi_locations import DELHI_LOCATIONS
        import math

        min_dist = float('inf')
        nearest = None

        for name, (loc_lat, loc_lon) in DELHI_LOCATIONS.items():

            dist = math.sqrt((lat - loc_lat)**2 + (lon - loc_lon)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = name

        return nearest

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            lat, lon = self.app_instance.offline_map.xy_to_lat_lon(touch.x, touch.y)

            nearest_loc = self.find_nearest_location(lat, lon)

            if nearest_loc:

                self.app_instance.location_spinner.text = nearest_loc.title()
                print(f"Selected: {nearest_loc.title()}")

            return True
        return super().on_touch_down(touch)
        '''