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
    add encoding and rate options i guess?
    add an image mask option so you can just bend a certain part of the image
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

class Bender:
    """
    Used for bending a given image.
    Bender.bend is used for bending to a single image, and
    Bender.bend_to_gif is used for bending the image into a sequence of images
    using different parameters for each one, usually for making an animation.

    Bender.tfm is a sox.Transformer, which is the part that does the "audio" editing.
    See https://pysox.readthedocs.io/en/latest/api.html for all the effects it can use.
    """
    
    def __init__(self, in_path):
        assert in_path.endswith(".bmp")
        self.tfm = sox.Transformer()
        self.tfm.set_input_format(file_type="raw", encoding="u-law", rate=72000, channels=1)
        self.tfm.set_output_format(file_type="raw", encoding="u-law", rate=72000, channels=1)
        self.tfm.set_globals(dither=True, verbosity=0)
        self.in_path = in_path
        self.in_head_path = ORGANS + in_path.replace("/","_") + "_head"
        self.in_body_path = ORGANS + in_path.replace("/","_") + "_body"
        self.body_length = guillotine.decapitate(in_path, self.in_head_path, self.in_body_path)

    def string_to_tfm_method(self, method_name):
        """
        Example: "echo" -> self.tfm.echo
        Used so we don't have to keep referring to the functions directly,
        so effects_and_kwargs stuff is easier to write,
        especially in MultiBender.
        """
        assert hasattr(self.tfm, method_name)
        return getattr(self.tfm, method_name)

    def bend(self, effects_and_kwargs=None, out_path=None):
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
        out_path = out_path or self.in_path[:-4]+"_bent.bmp"
        logging.info("Bending " + self.in_path + " to " + out_path)
        if effects_and_kwargs: 
            for effect, kwargs in effects_and_kwargs:
                #effect can either be a string specifying the tfm method to use,
                #or a reference to the tfm method itself.
                if isinstance(effect, str):
                    self.string_to_tfm_method(effect)(**kwargs)
                else:
                    assert effect.__self__ is self.tfm #should be a method of self.tfm
                    effect(**kwargs)
        
        try:
            self.tfm.build(self.in_body_path, TEMPBODYNAME)  #apply effects to bmp image array, output to TEMPBODYNAME
        except sox.core.SoxError: #probably due to invalid arguments
            logging.error("We probably used an invalid argument, but the following error message might not be informative.")
            logging.error("This seems to happen if an argument is too big or too small.")
            logging.error("So, here are the effects and arguments that we tried to use:")
            logging.error(str(self.tfm.effects)) #dump effects/arguments # list
            self.tfm.clear_effects() #clear the bad effects so we don't get stuck
            raise
        
        guillotine.rescale(TEMPBODYNAME, self.body_length) #correct image array size if necessary
        guillotine.recapitate(self.in_head_path, TEMPBODYNAME, out_path) #re-attach header to image array
        
        self.tfm.clear_effects()

    def bend_to_gif(self, effects_and_kwargs_sequence, frame_name_pattern=None):
        """
        Makes a gif out of a bunch of bends.
        Basically calls self.bend a bunch of times and
        compiles the frames into a gif.
        effects_and_kwargs_sequence should be a sequence of
        effects_and_kwargs things. (see self.bend for an example of those)
        """
        frame_name_pattern = frame_name_pattern or "frames/"+self.in_path[:-4]+"_{}.bmp"
        i = 0
        new_frame_paths = []
        for effects_and_kwargs in effects_and_kwargs_sequence:
            new_frame_path = frame_name_pattern.replace("{}",str(i).zfill(ZFILLAMOUNT))
            self.bend(effects_and_kwargs, new_frame_path)
            new_frame_paths.append(new_frame_path)
            i += 1
        animator.make_gif(new_frame_paths, gif_path=self.in_path+".gif")

class MultiBender: #doesn't work yet
    """
    Bends N images into N images.
    Would be used for bending a video or a gif.
    I haven't tested this one.
    """
    def __init__(self, gif_path=None, frame_paths=None):
        assert bool(frame_paths) ^ bool(gif_path) #frame_paths xor gif_path; exactly one should be supplied
        self.delays = None
        if gif_path:
            #dumps all the frames next to the gif. change later?
            frame_paths, self.delays = animator.split_gif(gif_path)
        
        self.benders = [Bender(frame_path) for frame_path in frame_paths]

    def bend_uniform(self, effects_and_kwargs, **kwargs):
        """
        Bends each image using the same effect, specified by effects_and_kwargs.
        Special case of bend_varying.
        """
        #call bend_varying but with the same effects_and_kwargs for every frame
        self.bend_varying([effects_and_kwargs] * len(self.benders), **kwargs)

    def bend_varying(self, effects_and_kwargs_sequence, gif_path=None, clobber=False):
        """
        Bends each image using the corresponding effect specified by effects_and_kwargs_sequence.
        If gif_path is specified, compiles the bent images into a gif.
        If clobber=True, clobbers (replaces) the original images with the bent ones.
        """
        new_frame_paths = []
        assert len(effects_and_kwargs_sequence) == len(self.benders)
        for i, bender in enumerate(self.benders):
            effects_and_kwargs = effects_and_kwargs_sequence[i]
            if clobber:
                new_frame_path = bender.in_path
            else:
                new_frame_path = bender.in_path[:-4] + "_bent.bmp"
            bender.bend(effects_and_kwargs, new_frame_path)
            new_frame_paths.append(new_frame_path)
        if gif_path:
            logging.info("animating bent gif: " + gif_path)
            animator.make_gif(new_frame_paths, gif_path=gif_path, delays=self.delays)

def sin_up_down(proportion):
    """
    Generates a sinusoidal curve. Useful for smoothly repeating gifs.
    Example: [sin_up_down(i/10) for i in range(10)] -> [0.0, 0.096, 0.345, 0.655, 0.905, 1.0, 0.905, 0.655, 0.345, 0.096]
    """
    return 1-(math.cos(proportion*2*math.pi)+1)/2

def test():
    b = Bender("porygon-z.bmp")
    b.bend({"highpass":{"frequency":500}})
    b.bend_to_gif([[(b.tfm.highpass, {"frequency":500+50*i})] for i in range(16)])

    b.bend_to_gif([[(b.tfm.allpass, {"frequency":500+500*sin_up_down(i/24)})] for i in range(24)]) #socks_goof

    #outdated:
    mb = MultiBender(sorted(glob.glob("frames/porygon-z_[0-9][0-9][0-9][0-9].bmp")))
    mb.bend_uniform({"echo":{"n_echos":6, "delays":[1024]*6, "decays":[0.4]*6}}, gif_path="gif.gif")

    #outdated:
    #b.bend({"echo":{"n_echos":9,"delays":[random.random() for _ in range(9)],"decays":[random.random() for _ in range(9)]}})
    #b.bend_to_gif([{"echo":{"n_echos":9,"delays":[(i+j+1)/39 for j in range(9)],"decays":[0.1 for _ in range(9)]}} for i in range(30)])
    #b.bend_to_gif([{"allpass":{"frequency":100+50*sin_up_down(i/30)}} for i in range(30)])
