import sockbend

# Here's the bmp we will bend today. Replace it if you want.
EXAMPLE_INPUT_BMP = "examples/socks.bmp"
# Here's the gif we will bend today. Replace it if you want.
EXAMPLE_INPUT_GIF = "examples/golb.gif"

# This object, the Bender, is used for bending a particular image.
b = sockbend.Bender(EXAMPLE_INPUT_BMP)

# Here's one way to bend the image.
# Here we call b.bend with - bear with me here - a sequence of tuples,
# with each tuple being of the form (command, keyword_arguments).
# The command should be a string (or a b.tfm method but don't worry about that)
# and the keyword arguments should be represented by a dict.
# These effects are just standard SoX effects, executed through pysox.
# Here's a list of the effects: https://pysox.readthedocs.io/en/latest/api.html
# out_path specifies where we'll save the bent image.
# By default, it will save to socks_bent.bmp (assuming the input image is socks.bmp).

b.bend([("highpass", {"frequency":500})], out_path="examples/ex1_highpass_500.bmp")

# Here's a more intricate example with multiple commands and arguments:
effects_and_kwargs = [
    (
        "highpass",
         {
             "frequency": 500,
             "width_q" : 0.6
             #Other highpass arguments would go here.
        }
    ),
    (
        "echo",
        {} #No arguments passed to echo. It will use default values.
    )
    #Other commands could go here. We could even do the same command multiple times.
]
b.bend(effects_and_kwargs, out_path="examples/ex1_highpass_500_0.6_echo.bmp")

# Here's a different style of using Bender.bend.
# It's harder and I don't recommend it; feel free to skip this example.
# It's not really fleshed out yet and you can't use it for MultiBenders or gifs,
# but you can use it for regular bends. It kinda looks better.
# Here we directly call the Bend
# This is equivalent to doing b.bend([("echo",{})], out_path="examples/ex_echo.bmp")
b.tfm.echo() #Queue echo effect
b.bend(out_path="examples/ex1_echo.bmp") #Bend with queued effects. This flushes the effects queue.


# Now, what about gifs?
# We can bend our single image into a gif with b.bend_to_gif.
# Bender.bend_to_gif takes a sequence of the effects_and_kwargs things used for Bender.bend.
# It bends the image for each effects_and_kwargs in the sequence,
# and then compiles them into a gif.
# By default, it saves the frames in a folder called "frames", so make sure that exists.
# It clobbers frames it has previously saved in the same way.
# You can change this by supplying the frame_name_pattern argument,
# but I recommend keeping a "frames" folder or similar to keep the frames out of the way.
# Here's an example using the allpass filter, but with an increasing frequency argument.
b.bend_to_gif(
    [[("allpass", {"frequency":500+50*i})] for i in range(24)],
    out_path="examples/ex1_allpass_500to1700.gif",
)
# That list comprehension is kind of messy,
# but it basically just does the same thing as the first example,
# except with frequency arguments [500, 550, 600, 650 ... 1650, 1700].

# What if we want our gifs to loop better?
# A handy tool for that is sockbend.sin_up_down.
# It generates a sin curve that goes from 0 to 1 to 0.
# Example: [sin_up_down(i/10) for i in range(10)] -> [0.0, 0.096, 0.345, 0.655, 0.905, 1.0, 0.905, 0.655, 0.345, 0.096]
# Here's an example like the last one, but with a seamless loop.
b.bend_to_gif(
    [[("allpass", {"frequency":500+1200*sockbend.sin_up_down(i/24)})] for i in range(24)],
    out_path="examples/ex1_allpass_500to1700to500.gif",
)


# What if we already have a gif and we want to bend it into another gif?
# For that, we'll want to use a MultiBender.
# I'm not confident with how the MultiBender is used. I think it could be made more elegant.
# For now, here's how it works. Let's bass-boost a gif.
mb = sockbend.MultiBender(EXAMPLE_INPUT_GIF)
mb.bend_uniform(
    [
        (
            "bass",
            {
                "gain_db": 1.5
            }
        )
    ],
    gif_path="examples/ex2_bass_0.2.gif"
)

# In that example, we applied the same effect to every frame.
# Here, we apply a varying-intensity effect to the frames.
# First, how many frames does the gif have?
n = mb.number_of_frames
# Let's use that information to make a loop with sin_up_down.
mb.bend_varying(
    [
        [
            (
                "bass",
                {
                    "gain_db": 0.2 + 2.0 * sockbend.sin_up_down(i/n)
                }
            )
        ] for i in range(n)
    ],
    gif_path="examples/ex2_bass_0.2to2.2to0.2.gif"
)

# Here's a similar one. I like the allpass filter.
mb.bend_varying(
    [
        [
            (
                "allpass",
                {
                    "frequency": 500 + 1200 * sockbend.sin_up_down(i/n)
                }
            )
        ] for i in range(n)
    ],
    gif_path="examples/ex2_allpass_500to1700to500.gif"
)
