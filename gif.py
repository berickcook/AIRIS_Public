import imageio.v2 as imageio
import os

img_dir = f"./doc/sav"
all_files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.endswith('.png')]
images = [imageio.imread(f) for f in all_files]
imageio.mimsave("doc/img/03_movie_3.gif", images)  #, fps=5)
