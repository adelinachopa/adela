import zipfile
import sys

apk_path = sys.argv[1] if len(sys.argv) > 1 else '/home/user/emk_game/bin/escapetoemk-1.0.0-arm64-v8a_armeabi-v7a-debug.apk'

with zipfile.ZipFile(apk_path, 'r') as z:
    for name in z.namelist():
        if 'pygame' in name.lower() and ('surface' in name.lower() or 'version' in name.lower()):
            print(name)
    
    # Also check for pygame version file
    for name in z.namelist():
        if 'pygame' in name.lower() and 'version' in name.lower():
            print(f"\nFound version file: {name}")
            try:
                data = z.read(name)
                print(data.decode('utf-8', errors='replace')[:500])
            except:
                pass