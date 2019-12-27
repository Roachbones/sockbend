# Sockbend
Python scripts for databending images by editing them as audio data using SoX.

## What's databending?
Databending is editing files as if they are of a different format. Specifically, Sockbend edits bitmap files as if they were audio files. You can do this with Audacity, but it's slow and error-prone; you have to be careful not to destroy the header data or make the image array the wrong size. Sockbend takes care of both of these limitations and lets you databend images through the Python shell. It can also make gifs. Examples are in the examples folder and the examples.py script.

## Requirements
Sockbend requires pysox and wand, which in turn require installations of SoX and ImageMagick. Sorry if that's a pain to set up.
