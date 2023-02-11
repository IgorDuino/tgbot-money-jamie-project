from main import generate_image
from PIL import Image
import urllib.request
import io


if __name__ == '__main__':
    fd = urllib.request.urlopen("https://i.pinimg.com/originals/77/04/c4/7704c4194ec9d87d1ac5478c836ae061.png")
    image_file = io.BytesIO(fd.read())
    im = Image.open(image_file)

    image = generate_image(0, "Tester's cat", 100,
                           im,
                           "https://i.pinimg.com/originals/77/04/c4/7704c4194ec9d87d1ac5478c836ae061.png")
    image.show()
