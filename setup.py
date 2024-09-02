from setuptools import setup, find_packages

setup(
    name="microbellm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "tqdm",
        "colorama",
        "openai",
    ],
    entry_points={
        "console_scripts": [
            "microbeLLM=microbellm.microbellm:main",
        ],
    },
    package_data={
        "microbellm": ["*.py", "*.txt"],  # Include all .py and .txt files
    },
    include_package_data=True,
)