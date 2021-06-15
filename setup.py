from setuptools import setup

setup(
    name='pyattack',
    version='0.4.1',
    url='',
    license='Proprietary',
    author='geoscan',
    author_email='info@geoscan.aero',
    description='PyAttack',
    setup_requires=['wheel'],
    install_requires=[
        'pymavlink',
        'numpy>=1.20.0',
        'opencv-contrib-python>=4.5.2.54',
        'PySide2>=5.15.2,<5.16',
        'scipy>=1.6.3',
        'matplotlib>=3.4.2',
        'keyboard>=0.13.5',
    ],
)
