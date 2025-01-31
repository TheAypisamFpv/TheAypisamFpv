from math import ceil
import cv2
import numpy as np
from PIL import Image

# Parameters
videoPath = "Bad Apple.mp4"  # Path to the input video
outputGif = "Bad Apple.gif"  # Name of the generated GIF
height = 7  # Height of the GitHub heatmap (7 pixels)
width = 52  # Max width (number of weeks visible on GitHub)
frameSkip = 2  # Number of frames to skip to speed up animation

# GitHub pixels paths
githubPixelsPaths = ["pixels/pixel0.png", "pixels/pixel1.png", "pixels/pixel2.png", "pixels/pixel3.png", "pixels/pixel4.png"]
pixelNum = len(githubPixelsPaths)

# Load the pixel images
githubPixels = [Image.open(path) for path in githubPixelsPaths]

pixelWidth = githubPixels[0].width
pixelHeight = githubPixels[0].height

# Generate the initial random commit pixels with a bias towards pixel0
initialPixels = np.clip(np.random.normal(1, 1, (height, width)), 0, pixelNum-1).astype(int)

# Initialize pixelReplaced array
pixelReplaced = np.zeros((height, width), dtype=int)

# Load the video
cap = cv2.VideoCapture(videoPath)
frames = []
frameCount = 0

videoLenght = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
videoFps = cap.get(cv2.CAP_PROP_FPS)

print("Processing Video...", end="\r")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Resize the frame while maintaining aspect ratio
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    aspectRatio = frame.shape[1] / frame.shape[0]
    newWidth = int(height * aspectRatio)
    
    # Normalize pixels
    normalizedFrame = np.clip(frame / 255 * pixelNum-1, 0, pixelNum-1)
    normalizedResizedFrame = cv2.resize(normalizedFrame, (newWidth, height), interpolation=cv2.INTER_LINEAR)
    
    frames.append(normalizedResizedFrame)
    
    frameCount += 1
    if frameCount % frameSkip != 0:
        frames.pop()

    print(f"Processed Video frame {frameCount + 1}/{videoLenght}          ", end="\r")

cap.release()

print("Processing Video Done             \n")

# Create the GIF
imgFrames = []
for i, frame in enumerate(frames):
    img = Image.new("RGB", (width * pixelWidth, height * pixelHeight), (0, 0, 0))
    
    # Calculate the starting x position to center the video frame
    startX = (width - newWidth) // 2
    
    for y in range(height):
        for x in range(width):
            if startX <= x < startX + newWidth:
                videoIntensity = ceil(frame[y, x - startX])  # GitHub intensity level from video
                if videoIntensity >= initialPixels[y, x] and not pixelReplaced[y, x]:
                    initialPixels[y, x] = videoIntensity  # Replace with video intensity if brighter
                    pixelReplaced[y, x] = 1  # Mark pixel as replaced
                elif not pixelReplaced[y, x]:
                    videoIntensity = initialPixels[y, x]
            else:
                videoIntensity = initialPixels[y, x]
                
            pixelImg = githubPixels[videoIntensity]  # Corresponding pixel image
            img.paste(pixelImg, (x * pixelWidth, y * pixelHeight))
    
    imgFrames.append(img)
    print(f"Processed GIF frame {i + 1}/{len(frames)}          ", end="\r")

print("Processed GIF Done             \n")

print("Saving GIF...", end="\r")

# calculate the duration of the gif using the video frame rate, and the number of frames skipped
duration = 1000 / (videoFps / frameSkip)  # 1 second / (frames per second / frameSkip)

imgFrames[0].save(
    outputGif, save_all=True, append_images=imgFrames[1:], loop=0, duration=duration
)

print(f"Saving GIF Done - {outputGif}")