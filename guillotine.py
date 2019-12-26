"""
Guillotine

For removing and reattaching BMP headers,
so that the image array can be safely databent
without destroying the header data.

Relevant bit of BMP format:
the image array starts at the address specified
at address 0xA.
"""

def decapitate(filename, headname=None, bodyname=None):
    """separate filename into two files. returns length of the body."""
    headname = headname or filename + "_head"
    bodyname = bodyname or filename + "_body"
    with open(filename, "rb") as file:
        bmp = file.read() #load the whole bmp into memory because we can
        blade = bmp[0xA] #the address that separates head and body
        head, body = bmp[:blade], bmp[blade:] #slice head and body
    with open(headname, "wb") as headfile:
        headfile.write(head)
    with open(bodyname, "wb") as bodyfile:
        bodyfile.write(body)
    return len(body)

def recapitate(headname, bodyname, filename):
    with open(headname, "rb") as headfile, open(bodyname, "rb") as bodyfile:
        head, body = headfile.read(), bodyfile.read()
    with open(filename, "wb") as file:
        file.write(head + body)

def rescale(bodyname, length):
    """truncates or adds bytes to clean up bmp body"""
    with open(bodyname, "rb+") as bodyfile:
        body = bodyfile.read()
        body = body[:length]
        body = body + bytes(length - len(body)) #add 0x00. change later
        assert len(body) == length
        bodyfile.seek(0)
        bodyfile.write(body)