from setuptools import setup, find_packages

setup(
    name="coral-bleach-predictor",
    version="0.1.0",
    description="Aimed to predict coral bleach events triggered via temperatures changes at a global scale within the environmenetal science sector",
    author="Simona Tingleff Kardel <simonakardel@gmail.com>, Wanesa Wintmiller <>, Kengo Reimers Kato <kengo.kato15@gmail.com>",
    packages=find_packages(),  
    install_requires=[         
        "numpy",
        "requests",
    ],
    classifiers=[              
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)