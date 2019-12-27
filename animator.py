"""
Uses imagemagick to compile images into gifs.
I don't like imagemagick so this is kind of messy.
Basically just do makegif to make a gif.
"""

import glob
import wand.image
import wand.drawing
import wand.exceptions
import warnings

def makegif(framepaths, delay=8, gifpath=None):
    #framepaths = glob.glob(framenamepattern)
    #assert framepaths
    #framepaths.sort()
    animation = wand.image.Image()
    print("total frames to animate: ", len(framepaths))
    i = 0
    for framepath in framepaths:
        print(i, end=" ")
        with warnings.catch_warnings(record=True) as w: #ignore CorruptImageWarning
            #warnings.simplefilter("ignore")
            frame = wand.image.Image(filename=framepath)
            assert len(w) <= 1
            #for some reason pylint can't see wand.exceptions.CorruptImageWarning. i can't find it in wand source code either
            #pylint: disable=no-member
            assert not w or issubclass(w[0].category, wand.exceptions.CorruptImageWarning)

        frame.delay = delay
        frame.dispose = "background"
        d=wand.drawing.Drawing()
        d(frame)
        animation.sequence.append(frame)
        i += 1

    print("saving")
    animation.type = "optimize"
    gifpath = gifpath or framepaths[0][:-4]+".gif"
    animation.save(filename=gifpath)
    print("saved", gifpath)

def splitgif(gifpath):
    framepaths = []
    with wand.image.Image(filename=gifpath) as image:
        i = 0
        for frame in image.sequence:
            framepath = gifpath + "_" + str(i).zfill(4) + ".bmp"
            frameimage = wand.image.Image(frame)
            frameimage.compression = "no" #we want uncompressed bmp, not rle-encoded.
            frameimage.save(filename=framepath)
            framepaths.append(framepath)
            i += 1
    return framepaths

