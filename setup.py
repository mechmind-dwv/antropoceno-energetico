from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="antropoceno-energetico",
    version="0.1.0",
    author="Benjamín Cabeza Duran",
    author_email="ia.mechmind@gmail.com",
    description="Herramientas para investigación de forzamientos climáticos no-GEI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mechmind-dwv/antropoceno-energetico",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: Creative Commons Attribution License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
    install_requires=[
        line.strip() for line in open("requirements.txt").readlines()
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "ae-process=antropoceno.cli:main",
        ],
    },
)
