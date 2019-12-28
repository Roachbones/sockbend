"""
Guillotine

For removing and reattaching BMP headers,
so that the image array can be safely databent without destroying the header data.

Relevant bit of BMP format:
the image array starts at the address specified at address 0xA.
"""

def decapitate(bmp_path, head_path=None, body_path=None):
    """
    Separate bmp_path into two files,
    the header data (the "head") and the image array (the "body").
    Returns the length of the body (so we can rescale the modified body later)
    """
    head_path = head_path or bmp_path + "_head"
    body_path = body_path or bmp_path + "_body"
    with open(bmp_path, "rb") as file:
        bmp = file.read() #load the whole bmp into memory because we can
        blade = bmp[0xA] #the address that separates head and body
        head, body = bmp[:blade], bmp[blade:] #slice head and body
    with open(head_path, "wb") as head_file:
        head_file.write(head)
    with open(body_path, "wb") as body_file:
        body_file.write(body)
    return len(body)

def recapitate(head_path, body_path, bmp_path):
    """
    Attaches header data and image array data to make a bmp file.
    """
    with open(head_path, "rb") as head_file, open(body_path, "rb") as body_file:
        head, body = head_file.read(), body_file.read()
    with open(bmp_path, "wb") as file:
        file.write(head + body)

def rescale(body_path, length):
    """
    Truncates or adds bytes to clean up bmp body.
    We have to do this because image viewers often don't like
    when bmp image arrays aren't the right length."""
    with open(body_path, "rb+") as body_file:
        body = body_file.read()
        body = body[:length] #truncate
        #add null bytes to the end if necessary.
        #it might be more aesthetically pleasing to make this repeat bytes from the beginning?
        body = body + bytes(length - len(body))
        assert len(body) == length
        body_file.seek(0)
        body_file.write(body)
