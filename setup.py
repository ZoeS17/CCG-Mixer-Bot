#!/usr/bin/env python3
"""Sets up required dependencies to run the bot/logger."""


from setuptools import setup, find_packages

setup(
    name="CCG-Mixer-Bot",
    version="0.0.1",
    url="https://github.com/ZoeS17/CCG-Mixer-Bot",
    author="Zoe Kahala",
    author_email="Zoe.Alice.Kahala@gmail.com",
    description="Chat Logger/Bot framework for Mixer.",
    long_description="Chat Logger/Bot framework for Mixer. Based off Connor's code @ github.com/mixer/beam-client-python",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests", "tornado", "pwnlib", "beautifulsoup4"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Topic :: Communications :: Chat',
        'Topic :: Internet',
        'Topic :: Multimedia :: Video',
    ]
)
