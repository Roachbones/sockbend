import guillotine
import animator
import sox
import math
import logging
logging.getLogger('sox').setLevel(logging.ERROR) #suppress sox's complaints
logging.basicConfig(level=logging.DEBUG)
import glob

ZFILLAMOUNT = 4
ORGANS = "organs/"
TEMPBODYNAME = ORGANS + "temp.bmp_body"

class Bender():
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

        #effectkwargs example: {"highpass": {frequency:500}} #nvm
        #effects_and_kwargs example: [(self.tfm.highpass, {frequency:500}), (self.tfm.echo, {})]

    def bend(self, effects_and_kwargs, outfilename=None): #limited
        #one input image, one effect, one output
        outfilename = outfilename or self.infilepath[:-4]+"_bent.bmp"
        logging.info("Bending " + self.infilepath + " to " + outfilename)
        try:
            for effect, kwargs in effects_and_kwargs:
                effect(**kwargs)
        except sox.core.SoxError: #probably due to invalid arguments
            self.tfm.clear_effects()
            raise    

        self.tfm.build(self.inbodypath, TEMPBODYNAME)
        guillotine.rescale(TEMPBODYNAME, self.bodylength)
        guillotine.recapitate(self.inheadpath, TEMPBODYNAME, outfilename)
        
        self.tfm.clear_effects()

    def bend_to_gif(self, effectkwargslist, framenamepattern=None):
        framenamepattern = framenamepattern or "frames/"+self.infilepath[:-4]+"_{}.bmp"
        i = 0
        newframepaths = []
        for effectkwargs in effectkwargslist:
            newframepath = framenamepattern.replace("{}",str(i).zfill(ZFILLAMOUNT))
            self.bend(effectkwargs, newframepath)
            newframepaths.append(newframepath)
            i += 1
        animator.makegif(newframepaths, gifpath=self.infilepath+".gif")

class MultiBender(): # for videos or similar
    def __init__(self, framepaths):
        for framepath in framepaths:
            assert framepath.endswith(".bmp")
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
    return (1-(math.cos((proportion)*2*math.pi)+1)/2)

def test():
    b = Bender("porygon-z.bmp")
    b.bend({"highpass":{"frequency":500}})
    b.bend_to_gif([{"highpass":{"frequency":500+50*i}} for i in range(8)])

    mb = MultiBender(sorted(glob.glob("frames/porygon-z_[0-9][0-9][0-9][0-9].bmp")))
    mb.bend_uniform({"echo":{"n_echos":6, "delays":[1024]*6, "decays":[0.4]*6}}, gifpath="gif.gif")

    #b.bend({"echo":{"n_echos":9,"delays":[random.random() for _ in range(9)],"decays":[random.random() for _ in range(9)]}})
    #b.bend_to_gif([{"echo":{"n_echos":9,"delays":[(i+j+1)/39 for j in range(9)],"decays":[0.1 for _ in range(9)]}} for i in range(30)])
    #b.bend_to_gif([{"allpass":{"frequency":100+50*sin_up_down(i/30)}} for i in range(30)])
