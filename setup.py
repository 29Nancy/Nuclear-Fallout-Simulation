
import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing required packages...")
    
    packages = [
        'kivy',
        'numpy'
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def create_directory_structure():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        'assets'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory exists: {directory}")

def check_files():
    """Check if all required files are present"""
    print("\n📋 Checking required files...")
    
    required_files = [
        'main.py',
        'wseg_core.py', 
        'plume_model.py',
        'delhi_locations.py'
    ]
    
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")
            all_present = False
    
    # Check optional files
    optional_files = [
        'assets/delhi_map.jpeg'
    ]
    
    print("\nOptional files:")
    for file in optional_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"⚠️  {file} - Not found (will use placeholder)")
    
    return all_present

def run_tests():
    """Run basic tests to verify functionality"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test imports
        import numpy as np
        print("✅ NumPy import successful")
        
        # Test backend modules
        try:
            from wseg_core import calculate_isodose_contour_dimensions
            from plume_model import calculate_casualties  
            from delhi_locations import get_coordinates, DELHI_LOCATIONS
            print("✅ Backend modules import successful")
            
            # Test a simple calculation
            test_coords = get_coordinates("connaught place")
            if test_coords:
                print(f"✅ Location lookup test: {test_coords}")
            
            test_casualties = calculate_casualties(10, 10000)
            if test_casualties.get('fatalities', 0) > 0:
                print(f"✅ Casualty calculation test: {test_casualties['fatalities']:,} fatalities")
                
            test_plume = calculate_isodose_contour_dimensions(10, 20, "Ground")
            print(f"✅ Fallout calculation test: {len(test_plume)} contours")
            
        except ImportError as e:
            print(f"❌ Backend module test failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Basic import test failed: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Nuclear Fallout Simulator Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        return False
    
    # Create directories
    create_directory_structure()
    
    # Check files
    if not check_files():
        print("\n❌ Some required files are missing!")
        print("Please make sure you have created all the required Python files.")
        return False
    
    # Run tests
    if not run_tests():
        print("\n❌ Tests failed!")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nTo run the simulator:")
    print("  python main.py")
    print("\nMake sure you have:")
    print("• All required Python files in the same directory")
    print("• Optional: delhi_map.jpeg in the assets/ folder for map display")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)