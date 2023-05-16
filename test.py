import time
import board
import busio
import numpy as np
import adafruit_mlx90640
import matplotlib.pyplot as plt

print("Initializing MLX90640")
i2c = busio.I2C(board.SCL, board.SDA, frequency=800000) # setup I2C
mlx = adafruit_mlx90640.MLX90640(i2c) # begin MLX90640 with I2C comm
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ # set refresh rate
mlx_shape = (24, 32)
print("Initialized")

# Setup the figure for plotting
plt.ion() # enables interactive plotting
fig, ax = plt.subplots(figsize=(12, 7))
therm1 = ax.imshow(np.zeros(mlx_shape), vmin=0, vmax=60) # start plot with zeros
cbar = fig.colorbar(therm1) # setup colorbar for temps
cbar.set_label('Temperature [$^{\circ}$C]', fontsize=14) # colorbar label

frame = np.zeros((24*32,)) # setup array for storing all 768 temperatures
t_array = []
snapshot_count = 0
print("Starting loop")
while True:
    t1 = time.monotonic()
    try:
        mlx.getFrame(frame) # read MLX temperatures into frame var
        data_array = (np.reshape(frame, mlx_shape)) # reshape to 24x32
        therm1.set_data(np.fliplr(data_array)) # flip left to right
        therm1.set_clim(vmin=np.min(data_array), vmax=np.max(data_array)) # set bounds
        cbar.update_normal(therm1) # update colorbar range
        plt.title(f"Max Temp: {np.max(data_array):.1f}C")
        plt.pause(0.001) # required
        t_array.append(time.monotonic() - t1)
        print('Sample Rate: {0:2.1f}fps'.format(len(t_array) / np.sum(t_array)))

        # Save snapshot image
        snapshot_count += 1
        image_filename = f"snapshot_{snapshot_count}.png"
        fig.savefig(image_filename, dpi=150)
        print(f"Snapshot saved: {image_filename}")
    except ValueError:
        continue # if error, just read again
