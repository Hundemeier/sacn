from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='sacn',
    version='1.8.0',
    description='sACN / E1.31 module for easy handling of DMX data over ethernet',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://www.github.com/Hundemeier/sacn',
    author='Hundemeier',
    author_email='hundemeier99@gmail.com',
    license='MIT License',
    packages=find_packages(),
    keywords=['sacn e131 e1.31 dmx'],
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    zip_safe=False
)
