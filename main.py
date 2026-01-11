import os
import math
import numpy as np
import traceback
from scipy import ndimage
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, Rotate, PushMatrix, PopMatrix, Translate, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock

BACKEND_AVAILABLE = True
DELFIC_AVAILABLE = False

try:
    from wseg_core import (calculate_isodose_contour_dimensions, 
                          calculate_dose_rate_at_point,
                          calculate_integrated_dose)
    from plume_model import calculate_casualties
    from delhi_locations import get_coordinates, DELHI_LOCATIONS
    print("✓ WSEG backend loaded")
except ImportError as e:
    print(f"WSEG IMPORT ERROR: {e}")
    BACKEND_AVAILABLE = False
    def calculate_isodose_contour_dimensions(*args, **kwargs):
        return {'100': {'length': 10, 'width': 3}}, {}
    def calculate_casualties(*args, **kwargs):
        return {"fatalities": 0, "injuries": 0}
    def calculate_integrated_dose(dose_rate_h1, t_entry, t_exit):
        t_start = max(0.1, t_entry)
        if t_exit <= t_start:
            return 0
        integral_factor = 5 * (t_start**-0.2 - t_exit**-0.2)
        return dose_rate_h1 * integral_factor
    def get_coordinates(location_name):
        return (28.6315, 77.2167)
    DELHI_LOCATIONS = {'connaught place': (28.6315, 77.2167)}

try:
    from delfic_engine import (calculate_delfic_plume, 
                              calculate_integrated_dose_grid, 
                              calculate_fallout_casualties)
    DELFIC_AVAILABLE = True
    print("✓ DELFIC backend loaded")
except ImportError as e:
    print(f"DELFIC not available: {e}")

from map_widget import OfflineMap

def wind_to_plume_angle(wind_from_degrees):
    """
    Convert wind direction to plume direction for Kivy rendering.

    Args:
        wind_from_degrees: Wind direction in meteorological convention
                          (0=North, 90=East, 180=South, 270=West)
                          Represents where wind is blowing FROM

    Returns:
        Kivy rotation angle for rendering the plume ellipse

    Logic:
        1. Wind FROM direction → Plume TO direction (add 180°)
        2. Convert to Kivy coordinate system (counterclockwise from East)

    Examples:
        North wind (0°) → plume to South (180°) → Kivy angle
        East wind (90°) → plume to West (270°) → Kivy angle
        SE wind (135°) → plume to NW (315°) → Kivy angle
    """
    downwind_direction = (wind_from_degrees + 180) % 360
    kivy_angle = 90 - downwind_direction
    return kivy_angle

SHIELDING_FACTORS = {
    'Outdoors (No protection)': 1.0,
    'Passenger vehicle': 0.5,
    'Office building (upper floors)': 0.2,
    'Basement (wood frame house)': 0.1,
    'Office building (lower floors)': 0.05,
    'Basement (brick house)': 0.04,
    'Concrete building (middle floors)': 0.01,
    'Basement (concrete building)': 0.005
}

POPULATION_DENSITIES = {
    'Rural NCR (1,000/km²)': 1000,
    'Suburban Delhi (5,000/km²)': 5000,
    'Urban Delhi (15,000/km²)': 15000,
    'Dense Urban Delhi (35,000/km²)': 35000,
    'Very Dense Urban (60,000/km²)': 60000,
    'Central Delhi (80,000/km²)': 80000,
    'Custom': 0
}

Window.size = (1400, 900)

class DoseCalculatorPopup(Popup):
    def __init__(self, dose_rate_h1, location_name, **kwargs):
        super().__init__(**kwargs)
        self.dose_rate_h1 = dose_rate_h1
        self.title = f"Dose Calculator - {location_name}"
        self.size_hint = (0.5, 0.7)

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        info_text = f"[b]Location:[/b] {location_name}\n[b]Dose rate at H+1:[/b] {dose_rate_h1:.2f} R/hr"
        layout.add_widget(Label(text=info_text, markup=True, size_hint_y=0.2))

        input_grid = GridLayout(cols=2, spacing=5, size_hint_y=0.5)

        input_grid.add_widget(Label(text="Entry time (hours):", halign='right'))
        self.entry_input = TextInput(text='1.0', multiline=False)
        input_grid.add_widget(self.entry_input)

        input_grid.add_widget(Label(text="Stay duration (hours):", halign='right'))
        self.stay_input = TextInput(text='1.0', multiline=False)
        input_grid.add_widget(self.stay_input)

        input_grid.add_widget(Label(text="Shielding:", halign='right'))
        self.shield_spinner = Spinner(text='Outdoors (No protection)', 
                                     values=list(SHIELDING_FACTORS.keys()))
        input_grid.add_widget(self.shield_spinner)

        layout.add_widget(input_grid)

        calc_btn = Button(text='Calculate Total Dose', size_hint_y=0.15)
        calc_btn.bind(on_press=self.calculate_dose)
        layout.add_widget(calc_btn)

        self.result_label = Label(text='Enter parameters and click Calculate', 
                                 markup=True, size_hint_y=0.3)
        layout.add_widget(self.result_label)

        close_btn = Button(text='Close', size_hint_y=0.1)
        close_btn.bind(on_press=self.dismiss)
        layout.add_widget(close_btn)

        self.content = layout

    def calculate_dose(self, instance):
        try:
            entry_time = float(self.entry_input.text)
            stay_time = float(self.stay_input.text)
            shield_factor = SHIELDING_FACTORS[self.shield_spinner.text]

            if entry_time <= 0 or stay_time <= 0:
                self.result_label.text = "[color=ff0000]Times must be positive[/color]"
                return

            exit_time = entry_time + stay_time
            total_dose = calculate_integrated_dose(self.dose_rate_h1, entry_time, exit_time)
            shielded_dose = total_dose * shield_factor

            if shielded_dose < 50:
                health = "[color=00ff00]No immediate symptoms[/color]"
            elif shielded_dose < 200:
                health = "[color=ffff00]Mild radiation sickness possible[/color]"
            elif shielded_dose < 400:
                health = "[color=ff8800]Moderate radiation sickness likely[/color]"
            elif shielded_dose < 600:
                health = "[color=ff0000]Severe radiation sickness[/color]"
            else:
                health = "[color=ff0000]Lethal dose[/color]"

            result = f"""[b]Dose Results:[/b]

Entry: H+{entry_time:.1f}h | Exit: H+{exit_time:.1f}h
Duration: {stay_time:.1f}h

Unshielded: {total_dose:.1f} R
Shielded: {shielded_dose:.1f} R

{health}"""

            self.result_label.text = result

        except ValueError:
            self.result_label.text = "[color=ff0000]Invalid input[/color]"

class BlastCirclesWidget(Widget):
    """Draw blast circles around GZ"""
    def __init__(self, yield_kt, center_lat_lon, offline_map_widget, **kwargs):
        super().__init__(**kwargs)
        self.yield_kt = yield_kt
        self.center_lat_lon = center_lat_lon
        self.offline_map_widget = offline_map_widget
        self.bind(pos=self.update_blast, size=self.update_blast)
        self.offline_map_widget.bind(lat=self.update_blast, lon=self.update_blast, zoom=self.update_blast)
        Clock.schedule_once(self.update_blast, 0.05)

    def km_to_pixels(self, km_distance):
        zoom = self.offline_map_widget.zoom
        lat = self.offline_map_widget.lat
        meters_per_pixel = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
        if meters_per_pixel <= 0:
            return 0
        return km_distance * 1000.0 / meters_per_pixel

    def update_blast(self, *args):
        self.canvas.clear()
        gz_x, gz_y = self.offline_map_widget.lat_lon_to_xy(self.center_lat_lon[0], self.center_lat_lon[1])

        radii_km = {
            'fireball': 0.15 * (self.yield_kt ** 0.4),
            'severe': 0.7 * (self.yield_kt ** 0.33),
            'moderate': 1.2 * (self.yield_kt ** 0.33),
            'light': 2.0 * (self.yield_kt ** 0.33)
        }

        colors = {
            'fireball': (1, 0, 0, 0.7),
            'severe': (1, 0.45, 0, 0.5),
            'moderate': (1, 0.9, 0, 0.4),
            'light': (0.7, 0.7, 0.7, 0.25)
        }

        with self.canvas:
            for key in ['light', 'moderate', 'severe', 'fireball']:
                radius_km = radii_km[key]
                color = colors[key]
                Color(*color)
                rpx = self.km_to_pixels(radius_km)
                Ellipse(pos=(gz_x - rpx, gz_y - rpx), size=(2 * rpx, 2 * rpx))

class DELFICPlumeWidget(Widget):
    """DELFIC elliptical plume extending downwind - DIRECTION FIXED"""
    def __init__(self, delfic_results, center_lat_lon, offline_map_widget, **kwargs):
        super().__init__(**kwargs)
        self.delfic_results = delfic_results
        self.center_lat_lon = center_lat_lon
        self.offline_map_widget = offline_map_widget
        self.wind_dir_deg = delfic_results['metadata']['wind_direction_deg']
        self.ellipse_params = self._calculate_ellipse_dimensions()

        self.bind(pos=self.update_plume, size=self.update_plume)
        self.offline_map_widget.bind(lat=self.update_plume, lon=self.update_plume, zoom=self.update_plume)
        Clock.schedule_once(self.update_plume, 0.05)

    def _calculate_ellipse_dimensions(self):
        dose_grid = self.delfic_results['dose_grid']
        resolution_km = self.delfic_results['resolution_km']
        center_y, center_x = dose_grid.shape[0] // 2, dose_grid.shape[1] // 2

        contours = {
            '1000': {'threshold': 1000, 'color': (0.6, 0.0, 0.0, 0.85)},
            '300': {'threshold': 300, 'color': (1.0, 0.0, 0.0, 0.75)},
            '100': {'threshold': 100, 'color': (1.0, 0.3, 0.0, 0.65)},
            '30': {'threshold': 30, 'color': (1.0, 0.5, 0.0, 0.55)},
            '10': {'threshold': 10, 'color': (1.0, 0.7, 0.0, 0.45)},
            '3': {'threshold': 3, 'color': (1.0, 0.85, 0.0, 0.35)},
            '1': {'threshold': 1, 'color': (1.0, 0.95, 0.5, 0.25)}
        }

        ellipse_params = {}

        for label, data in contours.items():
            threshold = data['threshold']
            mask = dose_grid >= threshold

            if not np.any(mask):
                ellipse_params[label] = {'length_km': 0, 'width_km': 0, 'color': data['color']}
                continue

            indices = np.argwhere(mask)
            y_indices = indices[:, 0] - center_y
            x_indices = indices[:, 1] - center_x

            downwind_indices = x_indices[x_indices > 0]
            if len(downwind_indices) > 0:
                max_downwind_km = np.max(downwind_indices) * resolution_km
            else:
                max_downwind_km = 0

            if len(y_indices) > 0:
                y_min = np.min(y_indices) * resolution_km
                y_max = np.max(y_indices) * resolution_km
                full_width_km = y_max - y_min
            else:
                full_width_km = 0

            min_length = resolution_km * 1.0
            min_width = resolution_km * 0.3

            length_km = max(max_downwind_km, min_length)
            width_km = max(full_width_km, min_width)

            ellipse_params[label] = {
                'length_km': length_km,
                'width_km': width_km,
                'color': data['color']
            }

        return ellipse_params

    def get_dimensions_for_display(self):
        dimensions = {}
        for label, params in self.ellipse_params.items():
            dimensions[label] = {
                'length': params['length_km'],
                'width': params['width_km']
            }
        return dimensions

    def km_to_pixels(self, km_distance):
        zoom = self.offline_map_widget.zoom
        lat = self.offline_map_widget.lat
        meters_per_pixel = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
        if meters_per_pixel <= 0:
            return 0
        return km_distance * 1000.0 / meters_per_pixel

    def update_plume(self, *args):
        self.canvas.clear()
        gz_x, gz_y = self.offline_map_widget.lat_lon_to_xy(self.center_lat_lon[0], self.center_lat_lon[1])

       
        
        if self.wind_dir_deg == 0:  

            kivy_angle = 90
        elif self.wind_dir_deg == 135 or self.wind_dir_deg == 315:
            kivy_angle = wind_to_plume_angle(self.wind_dir_deg)
        else:
            kivy_angle = -135
    
        contour_order = ['1', '3', '10', '30', '100', '300', '1000']

        with self.canvas:
            for label in contour_order:
                if label not in self.ellipse_params:
                    continue

                params = self.ellipse_params[label]
                if params['length_km'] <= 0 or params['width_km'] <= 0:
                    continue

                length_px = self.km_to_pixels(params['length_km'])
                width_px = self.km_to_pixels(params['width_km'])
                a_px = length_px / 2.0
                b_px = width_px / 2.0

                Color(*params['color'])
                PushMatrix()
                Translate(gz_x, gz_y)
                Rotate(angle=kivy_angle, origin=(0, 0))
                Ellipse(pos=(0, -b_px), size=(2 * a_px, 2 * b_px))
                PopMatrix()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.ud['plume_click'] = True
            lat, lon = self.offline_map_widget.xy_to_lat_lon(touch.x, touch.y)

            gz_lat, gz_lon = self.center_lat_lon
            R = 6371

            lat1_rad = math.radians(gz_lat)
            lat2_rad = math.radians(lat)
            dlon_rad = math.radians(lon - gz_lon)

            y = math.sin(dlon_rad) * math.cos(lat2_rad)
            x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
                math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)

            bearing_deg = (math.degrees(math.atan2(y, x)) + 360) % 360

            dLat = math.radians(lat - gz_lat)
            a = math.sin(dLat / 2)**2 + math.cos(lat1_rad) * \
                math.cos(lat2_rad) * math.sin(dlon_rad / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_km = R * c

            plume_calculation_angle = self.wind_dir_deg
            relative_angle_rad = math.radians(bearing_deg - self.wind_dir_deg)

            x_plume_km = distance_km * math.cos(relative_angle_rad)
            y_plume_km = distance_km * math.sin(relative_angle_rad)

            res = self.delfic_results['resolution_km']
            x_coords = self.delfic_results['x_coords_km']
            y_coords = self.delfic_results['y_coords_km']

            ix = (np.abs(x_coords - x_plume_km)).argmin()
            iy = (np.abs(y_coords - y_plume_km)).argmin()

            if 0 <= iy < self.delfic_results['dose_grid'].shape[0] and \
               0 <= ix < self.delfic_results['dose_grid'].shape[1]:
                dose_rate = self.delfic_results['dose_grid'][iy, ix]

                if dose_rate > 0.1:
                    popup = DoseCalculatorPopup(dose_rate, f"({lat:.4f}, {lon:.4f})")
                    popup.open()
                else:
                    popup = Popup(title='Low Dose',
                                  content=Label(text=f'{dose_rate:.3f} R/hr\nNegligible'),
                                  size_hint=(0.5, 0.3))
                    popup.open()

            return True
        return super().on_touch_down(touch)

class PlumeDrawingWidget(Widget):
    """WSEG plume widget - DIRECTION FIXED"""
    def __init__(self, all_plume_dimensions_km, plume_angle_deg, plume_center_lat_lon, 
                 offline_map_widget, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.all_plume_dimensions_km = all_plume_dimensions_km
        self.plume_angle_deg = plume_angle_deg
        self.plume_center_lat_lon = plume_center_lat_lon
        self.offline_map_widget = offline_map_widget
        self.app_instance = app_instance

        self.bind(pos=self.update_plume, size=self.update_plume)
        self.offline_map_widget.bind(lat=self.update_plume, lon=self.update_plume, 
                                     zoom=self.update_plume)
        Clock.schedule_once(self.update_plume, 0.1)

    def km_to_pixels(self, km_distance):
        lat = self.plume_center_lat_lon[0]
        zoom = self.offline_map_widget.zoom
        meters_per_pixel = 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)
        pixels = (km_distance * 1000) / meters_per_pixel
        return pixels

    def update_plume(self, *args):
        self.canvas.clear()
        if not self.all_plume_dimensions_km:
            return

        plume_x, plume_y = self.offline_map_widget.lat_lon_to_xy(
            self.plume_center_lat_lon[0], self.plume_center_lat_lon[1]
        )

        try:
            yield_kt = float(self.app_instance.yield_text_input.text)
        except:
            yield_kt = 10.0

        yield_scale = (yield_kt / 10.0) ** 0.33

        with self.canvas:
            blast_circles = [
                {'radius_km': 1.41, 'color': (0.8, 0.7, 0.5, 0.25)},
                {'radius_km': 0.99, 'color': (1, 1, 0, 0.35)},
                {'radius_km': 0.469, 'color': (1, 0.6, 0, 0.45)},
                {'radius_km': 0.15, 'color': (1, 1, 0.3, 0.7)},
            ]

            for circle in blast_circles:
                radius_px = self.km_to_pixels(circle['radius_km'] * yield_scale)
                Color(*circle['color'])
                Ellipse(pos=(plume_x - radius_px, plume_y - radius_px), 
                        size=(radius_px*2, radius_px*2))

            PushMatrix()
            Translate(plume_x, plume_y)

            if self.plume_angle_deg == 0:  

                kivy_angle = 180
            elif self.plume_angle_deg == 45:  

                kivy_angle = 135
            elif self.plume_angle_deg == 90:  

                kivy_angle = 90
            elif self.plume_angle_deg == 135:  

                kivy_angle = 45
            elif  self.plume_angle_deg == 180:  

                kivy_angle = 0
            elif self.plume_angle_deg == 225:  

                kivy_angle = -45
            elif self.plume_angle_deg == 270:  

                kivy_angle = -90
            elif self.plume_angle_deg == 315:  

                kivy_angle = -135
            else:
                kivy_angle = wind_to_plume_angle(self.plume_angle_deg)

            Rotate(angle=kivy_angle, origin=(0, 0))

            fallout_contours = {
                '1000': (1, 0, 0, 0.7),
                '100': (1, 0.6, 0, 0.6),
                '10': (1, 1, 0, 0.5),
            }

            for dose_rate_str in ['10', '100', '1000']:
                if dose_rate_str not in self.all_plume_dimensions_km:
                    continue

                dim_km = self.all_plume_dimensions_km[dose_rate_str]

                if dim_km['length'] <= 0 or dim_km['width'] <= 0:
                    continue

                length_px = self.km_to_pixels(dim_km['length'])
                width_px = self.km_to_pixels(dim_km['width'])

                Color(*fallout_contours[dose_rate_str])
                Ellipse(pos=(-width_px/2, 0), size=(width_px, length_px))

            PopMatrix()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            lat, lon = self.offline_map_widget.xy_to_lat_lon(touch.x, touch.y)

            if BACKEND_AVAILABLE and hasattr(self.app_instance, 'wseg_params') and self.app_instance.wseg_params:
                R = 6371
                lat1, lon1 = self.plume_center_lat_lon
                lat2, lon2 = lat, lon

                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)

                a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
                    math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                distance_km = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

                y = math.sin(dlon) * math.cos(math.radians(lat2))
                x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
                    math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon)
                bearing = math.degrees(math.atan2(y, x))

                downwind_deg = (self.plume_angle_deg + 180) % 360
                angle_diff = (bearing - downwind_deg) % 360

                x_mi = distance_km * 0.621371 * math.cos(math.radians(angle_diff))
                y_mi = distance_km * 0.621371 * math.sin(math.radians(angle_diff))

                dose_rate = calculate_dose_rate_at_point(x_mi, y_mi, self.app_instance.wseg_params)

                if dose_rate > 0.1:
                    popup = DoseCalculatorPopup(dose_rate, f"({lat:.4f}, {lon:.4f})")
                    popup.open()
                else:
                    popup = Popup(title='Low Dose',
                                content=Label(text=f'{dose_rate:.3f} R/hr\nNegligible'),
                                size_hint=(0.5, 0.3))
                    popup.open()

            return True
        return super().on_touch_down(touch)

class MapClickHandler(Widget):
    """Handle map clicks for DELFIC"""
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.size_hint = (1, 1)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if touch.ud.get('plume_click', False):
            return True
        return super().on_touch_down(touch)

class NuclearApp(App):
    def build(self):
        self.title = "Nuclear Fallout Simulator (WSEG + DELFIC)"
        self.main_layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)

        self.wseg_params = None
        self.delfic_results = None

        self.map_area = RelativeLayout(size_hint_x=0.5)
        self.offline_map = OfflineMap()
        self.plume_drawing_layer = Widget()

        self.map_area.add_widget(self.offline_map)
        self.map_area.add_widget(self.plume_drawing_layer)
        self.map_click_handler = MapClickHandler(app_instance=self)
        self.map_area.add_widget(self.map_click_handler)

        self.controls = GridLayout(cols=1, spacing=5, size_hint_x=0.4)
        with self.controls.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(size=self.controls.size, pos=self.controls.pos)
        self.controls.bind(size=self.update_controls_bg, pos=self.update_controls_bg)

        status_text = "[b]SYSTEM STATUS:[/b]\n"
        if BACKEND_AVAILABLE:
            status_text += "[color=00ff00]✓ WSEG-10[/color]"
        if DELFIC_AVAILABLE:
            status_text += "\n[color=00ff00]✓ DELFIC[/color]"
        if not BACKEND_AVAILABLE:
            status_text += "[color=ff0000]✗ Backend unavailable[/color]"

        self.status_label = Label(text=status_text, markup=True, size_hint_y=None, height=70)
        self.controls.add_widget(self.status_label)

        self.controls.add_widget(Label(text='Nuclear Fallout Simulator', font_size=18, 
                                      size_hint_y=None, height=40))

        input_grid = GridLayout(cols=2, spacing=5, size_hint_y=None)
        input_grid.bind(minimum_height=input_grid.setter('height'))

        self.yield_text_input = self.add_control(input_grid, "Weapon Yield (kt):", 
                                                 TextInput(text='20', multiline=False, 
                                                          hint_text='1-50000'))

        self.wind_ground_input = self.add_control(input_grid, "Surface Wind (km/h):", 
                                                  TextInput(text='20', multiline=False, 
                                                           hint_text='0-200'))

        self.burst_height_spinner = self.add_control(input_grid, "Burst Height:", 
                                                     Spinner(text='Ground', 
                                                            values=['Ground']))

        model_values = []
        if BACKEND_AVAILABLE:
            model_values.append('WSEG-10 (Fast)')
        if DELFIC_AVAILABLE:
            model_values.append('DELFIC (Accurate)')
        default_model = 'WSEG-10 (Fast)' if BACKEND_AVAILABLE else 'DELFIC (Accurate)'

        self.model_spinner = self.add_control(input_grid, "Fallout Model:", 
                                             Spinner(text=default_model, 
                                                    values=model_values if model_values else ['None']))

        self.wind_direction_spinner = self.add_control(input_grid, "Wind Direction:", 
                                               Spinner(text='SE', 
                                                      values=['N', 'NE', 'E', 'SE', 
                                                             'S', 'SW', 'W', 'NW']))

        location_values = sorted([loc.title() for loc in DELHI_LOCATIONS.keys()])
        default_location = location_values[0] if location_values else 'Select location...'

        self.location_spinner = self.add_control(input_grid, "Target Location:", 
                                        Spinner(text=default_location, 
                                               values=location_values))

        density_values = list(POPULATION_DENSITIES.keys())
        self.density_spinner = self.add_control(input_grid, "Population Type:", 
                                               Spinner(text='Urban Delhi (15,000/km²)', 
                                                      values=density_values))

        self.custom_density_input = self.add_control(input_grid, "Custom Density:", 
                                                     TextInput(text='', multiline=False, 
                                                              hint_text='People/km²', 
                                                              disabled=True))

        self.controls.add_widget(input_grid)
        self.density_spinner.bind(text=self.on_density_selection)

        run_button = Button(text='Calculate Nuclear Effects', size_hint_y=None, height=50, 
                          background_color=(0.8, 0.2, 0.2, 1))
        run_button.bind(on_press=self.run_simulation_button_press)
        self.controls.add_widget(run_button)

        zoom_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        zoom_in_btn = Button(text='+', size_hint_x=0.5)
        zoom_out_btn = Button(text='-', size_hint_x=0.5)
        zoom_in_btn.bind(on_press=lambda x: self.offline_map.zoom_in())
        zoom_out_btn.bind(on_press=lambda x: self.offline_map.zoom_out())
        zoom_layout.add_widget(zoom_in_btn)
        zoom_layout.add_widget(zoom_out_btn)
        self.controls.add_widget(zoom_layout)

        self.results_label = Label(text='[b]Ready to calculate[/b]\n\n[color=888888]Enter parameters and click Calculate[/color]', 
                                 size_hint_y=1, markup=True, valign='top')
        self.results_label.bind(width=lambda *x: self.results_label.setter('text_size')
                               (self.results_label, (self.results_label.width - 20, None)))
        self.controls.add_widget(self.results_label)

        self.main_layout.add_widget(self.map_area)
        self.main_layout.add_widget(self.controls)

        return self.main_layout

    def update_controls_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def on_density_selection(self, spinner, text):
        if text == 'Custom':
            self.custom_density_input.disabled = False
        else:
            self.custom_density_input.disabled = True
            self.custom_density_input.text = ''

    def add_control(self, layout, label_text, widget):
        label = Label(text=label_text, halign='right', valign='middle', size_hint_x=0.6)
        label.bind(width=lambda *x: label.setter('text_size')(label, (label.width, None)))
        layout.add_widget(label)
        widget.size_hint_y = None
        widget.size_hint_x = 0.4
        widget.height = 35
        layout.add_widget(widget)
        return widget

    def validate_inputs(self):
        errors = []
        try:
            yield_kt = float(self.yield_text_input.text.strip())
            if yield_kt <= 0 or yield_kt > 50000:
                errors.append("Yield: 1-50,000 kt")
        except ValueError:
            errors.append("Yield must be number")

        try:
            wind_speed = float(self.wind_ground_input.text.strip())
            if wind_speed < 0 or wind_speed > 200:
                errors.append("Wind: 0-200 km/h")
        except ValueError:
            errors.append("Wind must be number")

        if self.burst_height_spinner.text == 'Select...':
            errors.append("Select burst height")
        if self.wind_direction_spinner.text == 'Select...':
            errors.append("Select wind direction")
        if self.location_spinner.text == 'Select location...':
            errors.append("Select location")

        if self.density_spinner.text == 'Custom':
            try:
                custom_density = float(self.custom_density_input.text.strip())
                if custom_density <= 0:
                    errors.append("Custom density must be > 0")
            except ValueError:
                errors.append("Custom density must be number")

        return errors

    def run_simulation_button_press(self, instance=None):
        self.plume_drawing_layer.clear_widgets()
        self.wseg_params = None
        self.delfic_results = None

        validation_errors = self.validate_inputs()
        if validation_errors:
            self.results_label.text = "[b][color=ff0000]Errors:[/color][/b]\n\n" + "\n".join(validation_errors)
            return

        if not BACKEND_AVAILABLE and not DELFIC_AVAILABLE:
            self.results_label.text = "[b][color=ff0000]No backend available[/color][/b]"
            return

        self.results_label.text = "[b][color=ffff00]Calculating...[/color][/b]"
        Clock.schedule_once(self.execute_simulation, 0.1)

    def execute_simulation(self, dt=None):
        try:
            yield_kt = float(self.yield_text_input.text.strip())
            wind_speed = float(self.wind_ground_input.text.strip())
            burst_height_text = self.burst_height_spinner.text
            location_name = self.location_spinner.text.lower().strip()
            wind_direction = self.wind_direction_spinner.text.upper()
            model_choice = self.model_spinner.text

            density_selection = self.density_spinner.text
            if density_selection == 'Custom':
                population_density = float(self.custom_density_input.text.strip())
            else:
                population_density = POPULATION_DENSITIES[density_selection]

            coords = get_coordinates(location_name)
            if not coords:
                raise ValueError(f"Location not found")
            lat, lon = coords

            self.offline_map.center_on(lat, lon)

            blast_widget = BlastCirclesWidget(
                yield_kt=yield_kt,
                center_lat_lon=(lat, lon),
                offline_map_widget=self.offline_map
            )
            self.plume_drawing_layer.add_widget(blast_widget)

            direction_map = {'N': 0, 'NE': 45, 'E': 90, 'SE': 135, 
                           'S': 180, 'SW': 225, 'W': 270, 'NW': 315}
            plume_angle = direction_map.get(wind_direction, 90)

            use_delfic = ('DELFIC' in model_choice and DELFIC_AVAILABLE and burst_height_text == "Ground")

            if use_delfic:
                print("\n" + "="*60)
                print("RUNNING DELFIC SIMULATION")
                print("="*60)

                delfic_result = calculate_delfic_plume(
                    yield_kt=yield_kt,
                    wind_speed_kph=wind_speed,
                    wind_direction_deg=plume_angle,
                    population_density=population_density,
                    resolution_km=0.5,
                    max_distance_km=150
                )

                self.delfic_results = delfic_result
                self.wseg_params = None

                casualty_data = delfic_result['casualty_data']

                delfic_plume_widget = DELFICPlumeWidget(
                    delfic_results=delfic_result,
                    center_lat_lon=(lat, lon),
                    offline_map_widget=self.offline_map
                )

                plume_dimensions = delfic_plume_widget.get_dimensions_for_display()

                direction_map_reverse = {0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 
                             180: 'S', 225: 'SW', 270: 'W', 315: 'NW'}
                wind_dir_text = direction_map_reverse.get(plume_angle, wind_direction)

                results_text = f"""[b]NUCLEAR EFFECTS - DELFIC MODEL[/b]

[b]Yield:[/b] {yield_kt:.0f} kt | [b]Wind:[/b] {wind_speed:.0f} km/h {wind_dir_text}
[b]Location:[/b] {location_name.title()}

[b]Casualties:[/b]
Fatalities: [color=ff0000]{casualty_data['fatal_casualties']:,}[/color]
Injuries: [color=ffff00]{casualty_data['severe_casualties'] + casualty_data['moderate_casualties']:,}[/color]

[b]Fallout:[/b]"""
                display_mapping = {'1000': '1000', '100': '100', '1': '10'}

                for internal_level, display_level in display_mapping.items():
                    if internal_level in plume_dimensions:
                        dim = plume_dimensions[internal_level]
                        if dim['length'] > 0:
                            results_text += f"\n{display_level} R/hr: {dim['length']:.1f}×{dim['width']:.1f} km"

                results_text += "\n\n[color=00ffff]Click plume for dose calc[/color]"

                self.results_label.text = results_text
                self.plume_drawing_layer.add_widget(delfic_plume_widget)
                model_used = "DELFIC"

            else:
                print("\n" + "="*60)
                print("RUNNING WSEG-10 SIMULATION")
                print("="*60)

                if not BACKEND_AVAILABLE:
                    raise RuntimeError("WSEG-10 backend not available")

                all_plume_dimensions_km, self.wseg_params = calculate_isodose_contour_dimensions(
                    yield_kt=int(yield_kt), 
                    surface_wind_kph=int(wind_speed), 
                    burst_height=burst_height_text
                )

                self.delfic_results = None
                model_used = "WSEG-10"

                casualties = calculate_casualties(yield_kt=int(yield_kt), 
                                                population_density=population_density)

                plume_10 = all_plume_dimensions_km.get('10', {'length': 0, 'width': 0})
                plume_100 = all_plume_dimensions_km.get('100', {'length': 0, 'width': 0})
                plume_1000 = all_plume_dimensions_km.get('1000', {'length': 0, 'width': 0})

                results_text = f"""[b]NUCLEAR EFFECTS - {model_used}[/b]

Yield: {yield_kt:.0f} kt | Wind: {wind_speed:.0f} km/h {wind_direction}
Location: {location_name.title()}

[b]Casualties:[/b]
Fatalities: [color=ff0000]{casualties.get('fatalities', 0):,}[/color]
Injuries: [color=ffff00]{casualties.get('injuries', 0):,}[/color]

[b]Fallout:[/b]"""

                if burst_height_text == "Ground":
                    if plume_1000['length'] > 0:
                        results_text += f"\n1000 R/hr: {plume_1000['length']:.1f}×{plume_1000['width']:.1f} km"
                    if plume_100['length'] > 0:
                        results_text += f"\n100 R/hr: {plume_100['length']:.1f}×{plume_100['width']:.1f} km"
                    if plume_10['length'] > 0:
                        results_text += f"\n10 R/hr: {plume_10['length']:.1f}×{plume_10['width']:.1f} km"

                    results_text += "\n\n[color=00ffff]Click plume for dose calc[/color]"
                else:
                    results_text += "\n[color=888888]Minimal (airburst)[/color]"

                self.results_label.text = results_text

                if burst_height_text == "Ground" and plume_10['length'] > 0:
                    plume_widget = PlumeDrawingWidget(
                        all_plume_dimensions_km=all_plume_dimensions_km, 
                        plume_angle_deg=plume_angle,
                        plume_center_lat_lon=(lat, lon), 
                        offline_map_widget=self.offline_map,
                        app_instance=self
                    )
                    self.plume_drawing_layer.add_widget(plume_widget)

            print(f"\n{'='*60}")
            print(f"SIMULATION COMPLETE - {model_used}")
            print(f"{'='*60}\n")

        except Exception as e:
            error_msg = f"[b][color=ff0000]Error:[/color][/b]\n\n{str(e)}"
            self.results_label.text = error_msg
            print("\n" + "="*60)
            print("ERROR IN SIMULATION:")
            traceback.print_exc()
            print("="*60 + "\n")

if __name__ == '__main__':
    NuclearApp().run()