import qrcode


def create_qr(url, path="qr.png"):
    img = qrcode.make(url)
    img.save(path)

    return path