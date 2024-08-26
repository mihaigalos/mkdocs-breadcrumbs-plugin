from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mkdocs-breadcrumbs-plugin',
    version='0.1.10',
    description='Location-based breadcrumbs plugin for mkdocs.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='mkdocs plugin',
    url='https://github.com/mihaigalos/mkdocs-breadcrumbs-plugin',
    author='Mihai Galos',
    author_email='mihai@galos.one',
    license='MIT',
    python_requires='>=3.8',
    install_requires=[
        'mkdocs>=1.0.4',
        'mkdocs-material'
    ],
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'mkdocs-breadcrumbs-plugin = mkdocs_breadcrumbs_plugin.plugin:BreadCrumbs'
        ]
    }
)
