import numpy as np
from noise import pnoise2
import matplotlib.pyplot as plt

def diffuse_moisture(clouds, diffusion_rate = 0.1):
    rows = len(clouds)
    cols = len(clouds[0])
    cloud_array = np.array(clouds)
    kernel = np.array([[0, diffusion_rate, 0],
                       [diffusion_rate, 1- 4 * diffusion_rate, diffusion_rate],
                       [0, diffusion_rate, 0]])
    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            cloud_array[row][col] = np.sum(cloud_array[row - 1:row + 2, col - 1:col + 2] * kernel)
    cloud_array = np.clip(cloud_array, 0, 100)
    return cloud_array.tolist()

def generate_cloud_cover(width = 90, height = 60, scale = 20.0, octaves = 7, persistence = 0.3, lacunarity = 3.0, seed = 42):
    """
    Generates a 2D array of cloud-like noise values.
    
    Args:
        width (int): Width of the grid.
        height (int): Height of the grid.
        scale (float): Scale factor for noise (larger scale = smoother noise).
        octaves (int): Number of noise layers to combine.
        persistence (float): Amplitude reduction per octave.
        lacunarity (float): Frequency increase per octave.
        seed (int): Seed for noise generation.

    Returns:
        np.ndarray: 2D array of cloud-like noise values (0-255).
    """
    noise_array = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            # Normalize coordinates to scale
            nx = x / scale
            ny = y / scale
            # Generate Perlin noise value
            noise_value = pnoise2(nx, ny, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=seed)
            # Map noise value (-1.0 to 1.0) to (0 to 255)
            noise_array[y, x] = int((noise_value + 1) / 2 * 255)

    return noise_array

def main():
    # Parameters for cloud generation
    width = 90
    height = 60
    scale = 20.0        # Larger values = smoother clouds
    octaves = 7         # More octaves = more detail
    persistence = 0.3   # Controls amplitude of detail
    lacunarity = 3.0    # Controls frequency of detail
    seed = 42           # Ensures consistent results

    # Generate cloud cover noise
    cloud_cover = generate_cloud_cover(width, height, scale, octaves, persistence, lacunarity, seed)

    # Visualize the cloud cover
    plt.figure(figsize=(10, 6))
    plt.imshow(cloud_cover, cmap='gray', extent=(0, width, 0, height))
    plt.title("Simulated Cloud Cover")
    plt.xlabel("Width")
    plt.ylabel("Height")
    plt.colorbar(label="Cloud Cover (0=Clear, 255=Covered)")
    plt.show()

if __name__ == "__main__":
    main()