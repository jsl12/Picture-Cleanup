from setuptools import setup, find_packages

setup(
    name='Cleanup',
    version='0.1',
    description='System for cleaning up large quantities of files',
    author='John Lancaster',
    author_email='lancaster.js@gmail.com',
    install_requires=[
        'pandas',
        'pyyaml',
        'click',
        'exifread',
        'jupyterlab',
        'ipywidgets',
        'qgrid',
    ],
    packages=['cleanup']
)
