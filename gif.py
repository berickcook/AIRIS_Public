import imageio.v2 as imageio
import os

img_dir = f"./logs"
all_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.endswith('.png')]
images = [imageio.imread(f) for f in all_files]
imageio.mimsave("doc/img/01_movie.mp4", images, fps=5)
