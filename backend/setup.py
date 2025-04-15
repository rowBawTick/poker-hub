from setuptools import setup, find_packages

setup(
    name="poker-hud",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy==1.4.50",
        "lxml",
    ],
)
