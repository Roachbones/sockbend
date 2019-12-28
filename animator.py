"""
Uses imagemagick to compile images into gifs.
I don't like imagemagick so this is kind of messy.
Basically just do make_gif to make a gif.
"""

import glob
import warnings
import logging
from PIL import Image, ImageSequence
from pygifsicle import optimize

ZFILLAMOUNT = 4

def make_gif(frame_paths, save_kwargs, gif_path=None):
    """
    Just takes a bunch of image paths and turns it into a gif in a way that makes sense.
    Makes a good guess for where to save the gif if gif_path is unspecified.
    """
    gif_path = gif_path or frame_paths[0][:-4]+".gif"
    print("total frames to animate: ", len(frame_paths))
    frames = [Image.open(frame_path).quantize(dither=Image.NONE) for frame_path in frame_paths]
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], **save_kwargs)
    # PIL is bad at compressing gifs for some reason so we'll use gifsicle to optimize it
    optimize(gif_path)
    # for some reason, a round-trip through this module can make a gif twice as big. idk why

def split_gif(gif_path, frame_path_pattern="frames/frame_{}.bmp"):
    """
    Just splits a gif into frames in a way that makes sense.
    Returns frame_paths, save_kwargs
    save_kwargs is a dict of keyword arguments to be passed to PIL.Image.Image.save later.
    """
    frame_paths = []
    save_kwargs = {"duration":[]} #later we'll do im.save(... **save_kwargs)
    im = Image.open(gif_path)
    for i in ("transparency", "loop", "comment"): #relevant properties to save later
        if i in im.info:
            save_kwargs[i] = im.info[i]
    for i, frame in enumerate(ImageSequence.Iterator(im)):
        frame_path = frame_path_pattern.replace("{}",str(i).zfill(ZFILLAMOUNT))
        frame_paths.append(frame_path)
        im.save(frame_path)
        if "duration" in frame.info: #i imagine it wouldn't only be defined for SOME frames, right?
            save_kwargs["duration"].append(frame.info["duration"]) #append duration of current frame
    return frame_paths, save_kwargs

