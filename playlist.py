import pygame
import os
import eyed3

pygame.mixer.init()

def get_songname(current_song):
    
    track = eyed3.load(os.path.join("music", current_song))

    if track.tag:
        title = track.tag.title
        artist = track.tag.artist
        album = track.tag.album
        print(title, artist, album)
def toggle_pause():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()
        
def play_music(music_files, current_song = "", mode = 1):

    if not music_files:
        return
    n = 0
    if current_song != "":
        n = (music_files.index(current_song) + mode) % len(music_files)
    track = os.path.join("music", music_files[n])  # Get the next track
    pygame.mixer.music.load(track)
    pygame.mixer.music.play()

    return music_files[n]