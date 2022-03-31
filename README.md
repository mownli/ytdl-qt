# ytdl-qt
PyQt-application for downloading A/V files from sources supported by youtube-dl/yt-dlp/ffmpeg

![14-56-14](https://user-images.githubusercontent.com/101254975/159693738-c4da9696-0812-47bc-abb1-9495f65c230a.png)
## Features
- Ability to choose specific combinations of A/V quality
- History
- Customisable FFmpeg parameters
- Ability to directly stream A/V using a player of choice
## Dependencies
- python >= 3.8
- PyQt5
- yt-dlp
## Build/Installation
Download zip-file with the source code. Then run:

```
pip install <path-to-the-zip-file>
```

OR if you have all the dependencies installed: extract files from the archive, navigate to project's directory,

```
make
make install
```
In that case executable file is installed to `~/.local/bin/ytdl-qt.pyz`
