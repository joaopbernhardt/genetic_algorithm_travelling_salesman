import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# fig, ax = plt.subplots()

# x = np.arange(0, 2*np.pi, 0.01)
# line, = ax.plot(x, np.sin(x))


# def init():  # only required for blitting to give a clean slate.
#     line.set_ydata([np.nan] * len(x))
#     return line,


# def animate(i):
#     line.set_ydata(np.sin(x + i / 100))  # update the data.
#     return line,


# ani = animation.FuncAnimation(
#     fig, animate, init_func=init, interval=100, blit=True, save_count=50)

# # To save the animation, use e.g.
# #
# # ani.save("movie.mp4")
# #
# # or
# #
# # from matplotlib.animation import FFMpegWriter
# # writer = FFMpegWriter(fps=15, metadata=dict(artist='Me'), bitrate=1800)
# # ani.save("movie.mp4", writer=writer)

# plt.show()

########################################################


fig2 = plt.figure()

x = np.arange(-9, 10)
y = np.arange(-9, 10).reshape(-1, 1)
base = np.hypot(x, y)
ims = []
for add in np.arange(15):
    ims.append(plt.pcolor(x, y, base + add, norm=plt.Normalize(0, 30)),)

im_ani = animation.ArtistAnimation(fig2, ims, interval=50, repeat_delay=3000,
                                   blit=True)
# To save this second animation with some metadata, use the following command:
# im_ani.save('im.mp4', metadata={'artist':'Guido'})

plt.show()