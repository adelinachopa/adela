import os
import glob

# Patch alphablit.c directly in build directories
base = '/home/user/emk_game/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/pygame'
avx2_funcs = [
    'blit_blend_rgb_add_avx2',
    'blit_blend_rgb_sub_avx2',
    'blit_blend_rgb_mul_avx2',
    'blit_blend_rgb_min_avx2',
    'blit_blend_rgb_max_avx2',
    'blit_blend_rgba_add_avx2',
    'blit_blend_rgba_sub_avx2',
    'blit_blend_rgba_mul_avx2',
    'blit_blend_rgba_min_avx2',
    'blit_blend_rgba_max_avx2',
]

for arch_dir in ['arm64-v8a__ndk_target_21', 'armeabi-v7a__ndk_target_21']:
    alphablit = os.path.join(base, arch_dir, 'pygame', 'src_c', 'alphablit.c')
    if os.path.exists(alphablit):
        with open(alphablit, 'r') as f:
            content = f.read()
        for func in avx2_funcs:
            content = content.replace(
                func + '(&info)',
                '/* DISABLED ' + func + ' */ (void)0'
            )
        with open(alphablit, 'w') as f:
            f.write(content)
        print(f'Patched: {arch_dir}')
    else:
        print(f'Not found: {arch_dir}')

print('Done')