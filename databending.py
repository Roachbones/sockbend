"""
databending.py
Uses sox to edit bmp files as if they were sound files,
creating some cool effects.

todo:
    convert everything to snake_case
    add a big examples script
todo eventually?:
    add image rotation options for bending along pixel columns rather than rows
    add image channel separation options; chroma and luma (good idea emily)
"""

import guillotine #for isolating image arrays from bmp files
import animator #for compiling images into a gif

import sox #for "audio" editing
import math
import glob
import logging
logging.getLogger('sox').setLevel(logging.ERROR) #suppress sox's complaints
logging.basicConfig(level=logging.DEBUG)

ZFILLAMOUNT = 4 #for enumerated filenames, like snake_0002.bmp
ORGANS = "organs/" #folder used to temporarily store bmp parts
TEMPBODYNAME = ORGANS + "temp.bmp_body"

class Bender():
    """
    Used for bending a given image.
    Bender.bend is used for bending to a single image, and
    Bender.bend_to_gif is used for bending the image into a sequence of images
    using different parameters for each one, usually for making an animation.

    Bender.tfm is a sox.Transformer, which is the part that does the "audio" editing.
    See https://pysox.readthedocs.io/en/latest/api.html for all the effects it can use.
    """
    
    def __init__(self, infilepath):
        assert infilepath.endswith(".bmp")
        self.tfm = sox.Transformer()
        self.tfm.set_input_format(file_type="raw", encoding="u-law", rate=72000, channels=1)
        self.tfm.set_output_format(file_type="raw", encoding="u-law", rate=72000, channels=1)
        self.tfm.set_globals(dither=True, verbosity=0)
        self.infilepath = infilepath
        self.inheadpath = ORGANS + infilepath.replace("/","_") + "_head"
        self.inbodypath = ORGANS + infilepath.replace("/","_") + "_body"
        self.bodylength = guillotine.decapitate(infilepath, self.inheadpath, self.inbodypath)


    def bend(self, effects_and_kwargs=None, outfilename=None):
        """
        Bends one input image into one output image.
        Effects can be specified in order with effects_and_kwargs,
        like self.bend([(self.tfm.highpass, {"frequency":500}), (self.tfm.echo, {})]).
        
        Alternatively, you can call self.tfm.highpass(frequency=500) and self.tfm.echo(),
        and then just do self.bend() without specifying effects_and_kwargs.
        This takes more typing but can be easier because you can see the keyword argument hints
        in the IDE.
        
        Unintuitive note on tfm: Calling tfm.echo doesn't "really" apply the effect yet;
        it queues the effect to happen when tfm.build is called.
        See https://pysox.readthedocs.io/en/latest/example.html for a clearer example.
        """
        outfilename = outfilename or self.infilepath[:-4]+"_bent.bmp"
        logging.info("Bending " + self.infilepath + " to " + outfilename)
        if effects_and_kwargs: 
            for effect, kwargs in effects_and_kwargs:
                effect(**kwargs)
        
        try:
            self.tfm.build(self.inbodypath, TEMPBODYNAME) #apply effects to bmp image array, output to TEMPBODYNAME
        except sox.core.SoxError: #probably due to invalid arguments
            logging.error("We probably used an invalid argument, but the following error message might not be informative.")
            logging.error("This seems to happen if an argument is too big or too small.")
            logging.error("So, here are the effects and arguments that we tried to use:")
            logging.error(str(self.tfm.effects)) #dump effects/arguments list
            self.tfm.clear_effects() #clear the bad effects so we don't get stuck
            raise
        
        guillotine.rescale(TEMPBODYNAME, self.bodylength) #correct image array size if necessary
        guillotine.recapitate(self.inheadpath, TEMPBODYNAME, outfilename) #re-attach header to image array
        
        self.tfm.clear_effects()

    def bend_to_gif(self, effects_and_kwargs_sequence, frame_name_pattern=None):
        """
        Makes a gif out of a bunch of bends.
        Basically calls self.bend a bunch of times and
        compiles the frames into a gif.
        effects_and_kwargs_sequence should be a sequence of
        effects_and_kwargs things. (see self.bend for an example of those)
        """
        frame_name_pattern = frame_name_pattern or "frames/"+self.infilepath[:-4]+"_{}.bmp"
        i = 0
        new_frame_paths = []
        for effects_and_kwargs in effects_and_kwargs_sequence:
            new_frame_path = frame_name_pattern.replace("{}",str(i).zfill(ZFILLAMOUNT))
            self.bend(effects_and_kwargs, new_frame_path)
            new_frame_paths.append(new_frame_path)
            i += 1
        animator.makegif(new_frame_paths, gifpath=self.infilepath+".gif")

class MultiBender():
    """
    Bends N images into N images.
    Would be used for bending a video or a gif.
    I haven't tested this one.
    """
    def __init__(self, framepaths):
        for framepath in framepaths:
            assert framepath.endswith(".bmp")
            #maybe make a bunch of benders?
        self.framepaths = framepaths

    def bend_uniform(self, effectkwargs, **kwargs):
        self.bend_varying([effectkwargs] * len(self.framepaths), **kwargs)

    def bend_varying(self, effectkwargslist, gifpath=None, clobber=False):
        newframepaths = []
        assert len(effectkwargslist) == len(self.framepaths)
        for i in range(len(self.framepaths)):
            framepath = self.framepaths[i]
            effectkwargs = effectkwargslist[i]
            b = Bender(framepath)
            if clobber:
                newframepath = framepath
            else:
                newframepath = framepath[:-4] + "_bent.bmp"
            b.bend(effectkwargs, newframepath)
            newframepaths.append(newframepath)
        if gifpath:
            logging.info("animating bent gif: " + gifpath)
            animator.makegif(newframepaths, gifpath=gifpath)

def sin_up_down(proportion):
    """
    Generates a sinusoidal curve. Useful for smoothly repeating gifs.
    Example: [sin_up_down(i/10) for i in range(10)] -> [0.0, 0.096, 0.345, 0.655, 0.905, 1.0, 0.905, 0.655, 0.345, 0.096]
    """
    return (1-(math.cos((proportion)*2*math.pi)+1)/2)

def test():
    b = Bender("porygon-z.bmp")
    b.bend({"highpass":{"frequency":500}})
    b.bend_to_gif([[(b.tfm.highpass, {"frequency":500+50*i})] for i in range(16)])

    b.bend_to_gif([[(b.tfm.allpass, {"frequency":500+500*sin_up_down(i/24)})] for i in range(24)]) #socks_goof

    #outdated:
    mb = MultiBender(sorted(glob.glob("frames/porygon-z_[0-9][0-9][0-9][0-9].bmp")))
    mb.bend_uniform({"echo":{"n_echos":6, "delays":[1024]*6, "decays":[0.4]*6}}, gifpath="gif.gif")

    #outdated:
    #b.bend({"echo":{"n_echos":9,"delays":[random.random() for _ in range(9)],"decays":[random.random() for _ in range(9)]}})
    #b.bend_to_gif([{"echo":{"n_echos":9,"delays":[(i+j+1)/39 for j in range(9)],"decays":[0.1 for _ in range(9)]}} for i in range(30)])
    #b.bend_to_gif([{"allpass":{"frequency":100+50*sin_up_down(i/30)}} for i in range(30)])
