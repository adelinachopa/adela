import zipfile, os, sys

apk = sys.argv[1] if len(sys.argv) > 1 else 'bin/escapetoemk-1.0.0-arm64-v8a_armeabi-v7a-debug.apk'

with zipfile.ZipFile(apk, 'r') as z:
    for name in z.namelist():
        if 'surface.so' in name:
            print('Found:', name)
            z.extract(name, '/tmp/apk_check')
            extracted = os.path.join('/tmp/apk_check', name)
            ret = os.system('aarch64-linux-android-readelf -W -s ' + extracted + ' 2>/dev/null | grep -i -E "sse2|avx2|UND" | head -30')
            if ret != 0:
                print("  (no matching symbols or readelf failed)")
            os.unlink(extracted)