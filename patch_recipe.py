import os

recipe_path = '/home/user/emk_game/.buildozer/android/platform/python-for-android/pythonforandroid/recipes/pygame/__init__.py'
with open(recipe_path, 'r') as f:
    content = f.read()

# Add AVX2 patch after SSE2 patch
old = '''                with open(alphablit_path, 'w') as f:
                    f.write(content)
                print("PATCHED: Disabled PG_ENABLE_ARM_NEON blocks in alphablit.c")'''

new = '''                with open(alphablit_path, 'w') as f:
                    f.write(content)
                print("PATCHED: Disabled PG_ENABLE_ARM_NEON blocks in alphablit.c")

            # PATCH 1b: Disable AVX2 function calls in alphablit.c for ARM64
            # AVX2 functions (blit_blend_rgb_add_avx2, etc.) are called without #ifdef guard
            # They are implemented in simd_blitters_avx2.c (not compiled for Android)
            # We replace 'pg_has_avx2()' with '0' to disable the AVX2 code path
            if os.path.exists(alphablit_path):
                with open(alphablit_path, 'r') as f:
                    content = f.read()
                content = content.replace(
                    'pg_has_avx2()',
                    '0 /* DISABLED AVX2 for ARM64 compat */'
                )
                # Also comment out the AVX2 function calls themselves
                # (compiler may not eliminate dead code at -O0)
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
                for func in avx2_funcs:
                    content = content.replace(
                        func + '(&info)',
                        '/* DISABLED ' + func + ' */ (void)0'
                    )
                with open(alphablit_path, 'w') as f:
                    f.write(content)
                print("PATCHED: Disabled AVX2 function calls in alphablit.c")'''

content = content.replace(old, new)

with open(recipe_path, 'w') as f:
    f.write(content)
print('Recipe updated with AVX2 call removal')