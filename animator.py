"""
Uses imagemagick to compile images into gifs.
I don't like imagemagick so this is kind of messy.
Basically just do make_gif to make a gif.
"""

import glob
import wand.image
import wand.drawing
import wand.exceptions
import warnings

def make_gif(frame_paths, gif_path=None, delay=None, delays=None):
    """
    Just takes a bunch of image paths and turns it into a gif in a way that makes sense,
    so you don't have to get confused about imagemagick.
    Delays are measured in hundredths of a second.
    Either specify delay or delays. Or neither, in which case delay = 8.
    Makes a good guess for where to save the gif if gif_path is unspecified.
    """
    assert not (delay and delays)
    if not (delay or delays):
        delay = 8 #hundredths of a second
    if not delays:
        delays = [delay for _ in frame_paths]
    print("total frames to animate: ", len(frame_paths))
    with wand.image.Image() as animation:
        for i, frame_path in enumerate(frame_paths):
            print(i, end=" ")
            with warnings.catch_warnings(record=True) as w: #ignore CorruptImageWarning
                #warnings.simplefilter("ignore")
                with wand.image.Image(filename=frame_path) as frame:
                    animation.sequence.append(frame)
                assert len(w) <= 1
                #pylint: disable=no-member
                assert not w or issubclass(w[0].category, wand.exceptions.CorruptImageWarning)
            for frame in animation.sequence:
                frame.delay = delays[i]
                frame.dispose = "background"
                #d=wand.drawing.Drawing()
                #d(frame)

        print("saving")
        animation.type = "optimize"
        gif_path = gif_path or frame_paths[0][:-4]+".gif"
        animation.save(filename=gif_path)
        print("saved", gif_path)

def split_gif(gif_path):
    """
    Just splits a gif into frames in a way that makes sense
    so you don't have to get confused about imagemagick.
    Returns frame_paths, delays
    The delays can be used later to re-assemble the gif at the original speed.
    """
    frame_paths, delays = [], []
    with wand.image.Image(filename=gif_path) as image:
        image.coalesce() #kind of de-compress the frames
        for i, frame in enumerate(image.sequence):
            frame_path = gif_path + "_" + str(i).zfill(4) + ".bmp"
            frame_image = wand.image.Image(frame)
            frame_image.compression = "no" #we want uncompressed bmp, not rle-encoded.
            frame_image.save(filename=frame_path)
            frame_paths.append(frame_path)
            delays.append(frame.delay)
    return frame_paths, delays

