import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='http-razor',
    version='0.4',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'aiofiles',
        'http-router',
        'uvicorn',
        'uvloop',
        'multidict',
        'markupsafe',
        'python-multipart',
        'blinker '
    ],
    author="askfiy",
    author_email="c2323182108@gmail.com",
    url="https://github.com/askfiy/razor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.9"
)
