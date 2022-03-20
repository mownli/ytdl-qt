from setuptools import setup, find_packages

setup(
    name='ytdl_qt',
    version='1.0',
    packages=find_packages(),
    install_requires=['PyQt5', 'yt-dlp'],
    url='',
    license='',
    author='gyro',
    author_email='',
    description='',
    python_requires='>=3.8',
    entry_points={
        'gui_scripts': [
            'ytdl-qt=ytdl_qt.__main__:main',
        ],
    },
    include_package_data=True,
)
