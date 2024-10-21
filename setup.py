from setuptools import setup, find_packages

setup(
    name='pystacks',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'base32-crockford',
        'python-dotenv'  
    ],
    description='A Python library to interact with the Stacks blockchain',
    author='Justin Trollip',
    author_email='justin@ortege.io',
    url='https://github.com/Ortege-xyz/pystacks',
)
