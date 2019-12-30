from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()
 
setup(
    name="mvdef-lmmx",
    version="0.0.1",
    author="Louis Maddox",
    author_email="louismmx@gmail.com",
    description="Package to move functions and their import statements between files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lmmx/mvdef",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
    ],
    python_requires='>=3',
)
