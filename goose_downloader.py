import tkinter as tk
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
import subprocess
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import urlparse, urljoin
import os
import sys

# Global list to store PhotoImage objects and album links
photo_images = []
album_links = []

# Function to scrape the Bandcamp page and extract album data
def scrape_bandcamp():
    url = "https://goosetheband.bandcamp.com"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    albums = soup.find_all('li', class_='music-grid-item')

    album_data = []
    for album in albums[:8]:  # Limit to first 8 albums
        album_link = url + album.find('a')['href']
        album_image = album.find('img')['src']
        
        # Fix missing scheme in image URL
        parsed_url = urlparse(album_image)
        if not parsed_url.scheme:
            album_image = urljoin(url, album_image)
        
        album_data.append({'link': album_link, 'image': album_image})
        album_links.append(album_link)  # Store album link

    return album_data

# Function to download album using yt-dlp and display console log
def download_album(album_index, log_text):
    album_link = album_links[album_index]
    
    # Use the local yt-dlp binary
    yt_dlp_path = os.path.join(sys._MEIPASS, 'yt-dlp') if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), 'yt-dlp')
    command = f'{yt_dlp_path} --embed-thumbnail --add-metadata --replace-in-metadata "playlist" "/" "-" -o "%(artist)s - %(playlist)s\\%(playlist_index)s - %(track)s.%(ext)s" {album_link}'
    
    # Execute command with subprocess and capture output
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def update_log():
        for line in iter(process.stdout.readline, b''):
            log_text.insert(tk.END, line.decode('utf-8'))
            log_text.see(tk.END)
            root.update_idletasks()
        process.stdout.close()

    log_text.delete(1.0, tk.END)  # Clear previous log
    root.after(100, update_log)

# GUI setup
def create_gui():
    albums = scrape_bandcamp()

    global root
    root = tk.Tk()
    root.title("Goose Album Downloader")

    # Create grid layout for albums
    for i, album in enumerate(albums):
        row = i // 4
        col = i % 4

        # Fetch album image data
        try:
            response = requests.get(album['image'])
            img_data = response.content

            # Convert image data to PhotoImage
            img = Image.open(BytesIO(img_data))
            photo_img = ImageTk.PhotoImage(img)
            photo_images.append(photo_img)  # Store PhotoImage object in list

            # Display image in label
            label_img = tk.Label(root, image=photo_img)
            label_img.grid(row=row*2, column=col)  # Place image at even rows

            # Download button
            download_button = tk.Button(root, text="Download", command=lambda idx=i: download_album(idx, log_text))
            download_button.grid(row=row*2+1, column=col)  # Place button directly below the image
        
        except Exception as e:
            print(f"Error loading album image: {e}")

    # Log text box
    log_text = tk.Text(root, height=10, wrap='word')
    log_text.grid(row=8, columnspan=4, pady=20, padx=10, sticky='we')  # Place log text box below album grid

    root.mainloop()

# Run the GUI
if __name__ == "__main__":
    create_gui()
