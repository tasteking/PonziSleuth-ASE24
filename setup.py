"""
    PonziSleuth Package
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="PonziSleuth",  # Required
    version="0.1.0",  # Required
    package_dir={"": "src"},  # Optional
    packages=find_packages(where="src"),  # Required
    python_requires=">=3.10.14",
    install_requires=["setuptools>=68.2.2", "beautifulsoup4==4.12.3", "openai==1.23.6", "regex==2024.4.16", "slither-analyzer==0.10.2"],  # Optional
    entry_points={  # Optional
        "console_scripts": [
            "PonziSleuth=PonziSleuth:main",
        ]
    }
)