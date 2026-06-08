import os
from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


class Pygame2Recipe(CompiledComponentsPythonRecipe):
    """
    Recipe to build apps based on SDL2-based pygame.
    PATCHED: Disables SSE2 functions in alphablit.c for ARM64 compatibility.
    PATCHED: Disables AVX2 function calls in alphablit.c for ARM64 compatibility.
    PATCHED: Fixes distutils.ccompiler.spawn for Python 3.11+.
    """

    version = '2.1.0'
    url = 'https://github.com/pygame/pygame/archive/{version}.tar.gz'

    site_packages_name = 'pygame'
    name = 'pygame'

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png']
    call_hostpython_via_targetpython = False  # Due to setuptools
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()
            env = self.get_recipe_env(arch)
            env['ANDROID_ROOT'] = join(self.ctx.ndk.sysroot, 'usr')

            png = self.get_recipe('png', self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), '.libs')
            png_inc_dir = png.get_build_dir(arch)

            jpeg = self.get_recipe('jpeg', self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)

            sdl_mixer_includes = ""
            sdl2_mixer_recipe = self.get_recipe('sdl2_mixer', self.ctx)
            for include_dir in sdl2_mixer_recipe.get_include_dirs(arch):
                sdl_mixer_includes += f"-I{include_dir} "

            sdl2_image_includes = ""
            sdl2_image_recipe = self.get_recipe('sdl2_image', self.ctx)
            for include_dir in sdl2_image_recipe.get_include_dirs(arch):
                sdl2_image_includes += f"-I{include_dir} "

            setup_file = setup_template.format(
                sdl_includes=(
                    " -I" + join(self.ctx.bootstrap.build_dir, 'jni', 'SDL', 'include') +
                    " -L" + join(self.ctx.bootstrap.build_dir, "libs", str(arch)) +
                    " -L" + png_lib_dir + " -L" + jpeg_lib_dir + " -L" + arch.ndk_lib_dir_versioned),
                sdl_ttf_includes="-I"+join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_ttf'),
                sdl_image_includes=sdl2_image_includes,
                sdl_mixer_includes=sdl_mixer_includes,
                jpeg_includes="-I"+jpeg_inc_dir,
                png_includes="-I"+png_inc_dir,
                freetype_includes=""
            )
            open("Setup", "w").write(setup_file)

            # PATCH 1: Disable SSE2/NEON functions in alphablit.c for ARM64
            # pygame 2.1.3 uses PG_ENABLE_ARM_NEON which is auto-defined for __aarch64__
            # This causes calls to SSE2-named functions (alphablit_alpha_sse2_*)
            # whose implementations are in simd_blitters_sse2.c (not compiled for Android)
            alphablit_path = "src_c/alphablit.c"
            if os.path.exists(alphablit_path):
                with open(alphablit_path, 'r') as f:
                    content = f.read()
                # Replace all occurrences of PG_ENABLE_ARM_NEON guards
                content = content.replace(
                    '#if PG_ENABLE_ARM_NEON',
                    '#if 0 /* DISABLED SSE2 for ARM64 compat */'
                )
                with open(alphablit_path, 'w') as f:
                    f.write(content)
                print("PATCHED: Disabled PG_ENABLE_ARM_NEON blocks in alphablit.c")

            # PATCH 1b: Disable AVX2 function calls in alphablit.c for ARM64
            # AVX2 functions (blit_blend_rgb_add_avx2, etc.) are called without #ifdef guard
            # They are implemented in simd_blitters_avx2.c (not compiled for Android)
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
                print("PATCHED: Disabled AVX2 function calls in alphablit.c")

            # PATCH 2: Fix distutils.ccompiler.spawn for Python 3.11+
            # In Python 3.11, distutils.ccompiler.spawn was removed.
            # We replace it with distutils.spawn.spawn
            setup_py_path = "setup.py"
            if os.path.exists(setup_py_path):
                with open(setup_py_path, 'r') as f:
                    content = f.read()
                content = content.replace(
                    'distutils.ccompiler.spawn(cmd, dry_run=self.dry_run, **kwargs)',
                    'distutils.spawn.spawn(cmd)'
                )
                with open(setup_py_path, 'w') as f:
                    f.write(content)
                print("PATCHED: Fixed distutils.ccompiler.spawn in setup.py")

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL2'] = '1'
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = Pygame2Recipe()