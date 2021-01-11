from setuptools import setup, find_packages

setup(
    name='ytdl_qt',
    version='1.0',
    packages=find_packages(),
    install_requires=['PyQt5', 'pyperclip', 'youtube_dl'],
    url='',
    license='',
    author='gyro',
    author_email='',
    description='',
    python_requires='>=3',
    scripts=['data/ytdl-qt.py'],
)
