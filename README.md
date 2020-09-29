# Sockbend
![PySocks](https://raw.githubusercontent.com/Roachbones/Roachbones.github.io/master/python_sock_bent.png)

Python scripts for databending images by editing them as audio data using SoX.

## What's databending?
Databending is editing files as if they are of a different format. Specifically, Sockbend edits bitmap files as if they were audio files. This creates cool glitchy-looking distortions in the image. You can do this with Audacity, but it's slow and error-prone; you have to be careful not to destroy the header data or make the image array the wrong size. Sockbend takes care of both of these limitations and lets you databend images through the Python shell. It can also make gifs. Examples are in the examples folder and the examples.py script.

## Requirements
Sockbend requires [pysox](https://github.com/rabitt/pysox) and Pillow. If you're on Ubuntu, the following commands should install everything:

```
sudo apt install sox
pip3 install sox
git clone https://github.com/Roachbones/sockbend.git
```
