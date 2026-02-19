from setuptools import setup, Extension
from Cython.Build import cythonize
import os


def find_py_files(base_dir):
    extensions = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)
                module_path = full_path.replace("/", ".").replace("\\", ".")[:-3]

                extensions.append(
                    Extension(
                        module_path,
                        [full_path]
                    )
                )
    return extensions

extensions = []
extensions += find_py_files("sms")
extensions += find_py_files("challan_workflow")

setup(
    name="fulfillment-service",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "embedsignature": True,
            #"cdivision": True,
            #"nonecheck": False
        },
        #annotate=True,
        #force=True,
        #gdb_debug=False,
    ),
    zip_safe=False
)
