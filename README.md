Nuclear Fallout Simulation Using DELFIC and WSEG Models

📖 OVERVIEW

This project is an offline nuclear fallout simulation and visualization system designed to model radioactive fallout dispersion following a surface nuclear detonation. The application estimates fallout plume geometry, radiation dose rates, integrated radiation exposure, and population-level casualties using both physics-based and empirical modeling approaches.

The system is intended for educational, academic, and research purposes, enabling users to study post-detonation fallout behavior without requiring internet connectivity or real-time data sources.


🎯 OBJECTIVES

1. Simulate radioactive fallout dispersion after a nuclear detonation
2. Estimate radiation dose rates and integrated doses
3. Compare physics-based (DELFIC) and empirical (WSEG-10) fallout models
4. Visualize fallout plumes on an offline map
5. Assess population exposure and casualty estimates
6. Provide an interactive tool for post-detonation risk analysis


🧠 MODELS IMPLEMENTED

1️⃣ DELFIC Model (Physics-Based)

Fallout particle size stratification
Mushroom cloud stabilization and vertical distribution
Atmospheric transport with wind shear effects
Ground deposition of radioactive particles
Dose rate estimation and time integration
Casualty estimation based on radiation exposure


2️⃣ WSEG-10 Model (Empirical)

Elliptical fallout plume geometry
Dose rate decay laws
Integrated dose computation
Rapid casualty estimation
Suitable for fast, approximate fallout assessment




🗺️ KEY FEATURES

Fully offline operation
Interactive map-based visualization
User-defined inputs (yield, wind speed, wind direction, population density)
Fallout plume visualization (elliptical and contour-based)
Dose calculation at user-selected locations
Shielding and exposure duration analysis
Comparative modeling using two established fallout methods




🛠️ TECHNOLOGY STACK

Python
NumPy, SciPy – numerical computation
Kivy – graphical user interface
Offline OpenStreetMap tiles
OpenCV – contour rendering (optional)





⚙️ APPLICATION WORKFLOW

User selects the target location on the map
Weapon and meteorological parameters are entered
Fallout model (DELFIC or WSEG-10) is selected
Backend performs fallout computations
Fallout plume and dose fields are visualized
Casualty estimates and exposure statistics are generated
User can click on the map to compute local radiation dose




🗺️ OFFLINE MAP SETUP

Ensure offline OpenStreetMap tiles are available in the assets/ directory

The application does not require internet access during runtime




▶️ How to Run the Application

🔧 Prerequisites

Ensure the following are installed:

Python 3.9 or higher

pip (Python package manager)

System capable of running Kivy GUI applications


📦 Install Dependencies

It is recommended to use a virtual environment:

Create and activate virtual environment

Linux / macOS:  python -m venv venv
                source venv/bin/activate


Windows:  python -m venv venv
          venv\Scripts\activate


Install required packages
pip install numpy scipy kivy opencv-python



▶️ Run the Application

From the project root directory, execute:
python main.py
#The graphical user interface will launch automatically.





🧭 HOW TO USE THE APPLICATION

Step 1: Select Target Location

Choose a predefined location or click directly on the map to set the detonation point

Step 2: Enter Weapon Parameters

Weapon yield (kilotons)

Burst type (surface or airburst)

Wind speed (km/h)

Wind direction

Step 3: Choose Fallout Model

DELFIC – Physics-based, higher-fidelity simulation

WSEG-10 – Empirical, rapid estimation model

Step 4: Set Population Parameters

Select a predefined population density

Or

Enter a custom population density

Step 5: Run Simulation

Click “Calculate Nuclear Effects”

#Fallout plume and blast effects will be visualized on the map

Step 6: Analyze Results
View fallout plume geometry

Examine dose rate and integrated dose fields

Click any map location to compute radiation exposure

Review estimated casualties and affected areas


📊 OUTPUTS

Fallout plume visualization
Dose rate distribution (R/hr)
Integrated dose estimates (rem)
Casualty breakdown (fatal, severe, moderate, mild)
Affected area estimation

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/dc4dfcd8-bbaf-4f67-a0e9-c2acf2ed3dbc" />




📂 REPOSITORY STRUCTURE





<img width="740" height="276" alt="image" src="https://github.com/user-attachments/assets/e563db8f-7dd7-4455-af7a-76df18402970" />



🚨 DISCLAIMER

This project is intended strictly for educational, academic, and research purposes.
It does not support weapon design, targeting, or operational deployment.
All models are simplified and based on publicly available information.
