import os
import logging
import argparse
import time
import secrets  # Importing secrets.py
import mutagen
from mutagen.id3 import ID3, ID3NoHeaderError, TCON, COMM
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Function to search Spotify for a track and return genre
def get_genre(sp, artist, track):
    try:
        results = sp.search(q='artist:' + artist + ' track:' + track, type='track')
        items = results['tracks']['items']
        if len(items) > 0:
            track_id = items[0]['id']
            track_info = sp.track(track_id)
            artist_id = track_info['artists'][0]['id']
            artist_info = sp.artist(artist_id)
            genres = artist_info['genres']

            logging.debug(f"Retrieved genres for {artist} - {track}: {genres}")
            return genres[0] if genres else 'Unknown'  # Select the first genre or default to 'Unknown'
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 429:
            retry_after = int(e.headers.get('Retry-After', 1))
            logging.warning(f"Rate limiting, sleeping for {retry_after} seconds")
            time.sleep(retry_after)
            return get_genre(sp, artist, track)  
        else:
            logging.error(f"Spotify API error: {e}")
    except Exception as e:
        logging.error(f"Error during Spotify API call: {e}")
    return 'Unknown'

def output_metatdata(file_path):
    try:
        audiofile = mutagen.File(file_path, easy=False)
        if audiofile is not None:
            logging.info(f"\n\nSuccessfully read metadata for {file_path}")
            for key, value in audiofile.items():
                logging.info(f"{key}: {value}")
        else:
            logging.warning(f"\n\nNo metadata found for {file_path}")
        return audiofile
    except Exception as e:
        logging.error(f"\n\nError reading metadata for {file_path}: {e}")
        return None

def extract_metadata(file_path):
    try:
        # Load the file using mutagen
        audiofile = mutagen.File(file_path, easy=True)
        #logging.info(f"targeting file: {audiofile}")
        # Check if it's an MP3 file with ID3 tags
        if audiofile is not None: #and isinstance(audiofile, mutagen.id3.ID3FileType):
            # Extract artist, title, comments, and genre
            artist = audiofile.get('artist', [None])[0]
            title = audiofile.get('title', [None])[0]
            comments = audiofile.get('COMM::eng', [None])[0]  # Extracting comments, assuming 'eng' for English
            genre = audiofile.get('TCON', [None])[0]  # Extracting genre

            if artist and title:
                return artist, title, comments, genre
            else:
                logging.warning("Artist or title tag not found.")
                return None, None, None, None
        else:
            logging.error(f"The file {file_path} is not an MP3 file or does not contain ID3 tags")
            return None, None, None, None

    except Exception as e:
        logging.error(f"An error occurred while extracting metadata: {e}")
        return None, None, None, None

def updateComments(file_path, new_genre):
    try:
        # Try to load the ID3 tag, or create one if it doesn't exist
        try:
            audiofile = ID3(file_path)
        except ID3NoHeaderError:
            audiofile = ID3()

        # Check if the comments frame exists and read the current comments
        current_comments = ""
        if audiofile.getall("COMM"):
            for comm in audiofile.getall("COMM"):
                if comm.lang == 'eng':
                    current_comments = comm.text[0]
                    break

        # Update comments to include genre only if not already present
        genre_comment = f" Genre: {new_genre}"
        if genre_comment not in current_comments:
            new_comments = f"{current_comments}{genre_comment}" if current_comments else genre_comment
            # Update or add the COMM frame with the new comments
            audiofile.add(COMM(encoding=3, lang='eng', desc='', text=new_comments))

            # Save the changes back to the file
            audiofile.save(file_path)
            logging.info(f"Comments updated for {file_path}")
        else:
            logging.info("Genre already mentioned in comments, no update required.")

    except Exception as e:
        logging.error(f"An error occurred while updating comments: {e}")

def update_genre(file_path, genre):
    try:
        audiofile = mutagen.File(file_path, easy=True)

        if audiofile is not None:
            # Update the genre using dictionary-style assignment
            audiofile['genre'] = genre

            # Save the changes
            audiofile.save()
            logging.info(f"Genre updated to '{genre}' for {file_path}")
        else:
            logging.info(f"The file {file_path} is not an MP3 file or does not contain ID3 tags")
    except Exception as e:
        logging.error(f"An error occurred while updating the genre: {e}")

def process_file(sp, file_path):
    artist, title, comments, genre = extract_metadata(file_path)

    if artist and title:
        # Attempt to find a genre if not already tagged
        new_genre = get_genre(sp, artist, title) if genre is None else None

        # If a new genre is found and it's different from 'Unknown'
        if new_genre and new_genre != 'Unknown':
            # Check if comments exist and prepare them for update
            comments = "" if comments is None else comments
            
            # Format the genre comment and check if it's already in the comments
            genre_comment = f"Genre: {new_genre}"
            if genre_comment not in comments:
                # Append the new genre to the comments if it's not already mentioned
                new_comments = f"{comments} {genre_comment}".strip()
                updateComments(file_path, new_comments)
            else:
                logging.info("Genre already mentioned in comments, no update required.")
        elif genre:  # If an existing genre is found, check for comment update without altering the genre tag
            genre_comment = f"Genre: {genre}"
            if genre_comment not in comments:
                new_comments = f"{comments} {genre_comment}".strip()
                updateComments(file_path, new_comments)
            else:
                logging.info("Genre already mentioned in comments, no update required.")
        else:
            logging.warning(f"Genre for {artist} - {title} could not be determined or is already set.")
    else:
        logging.warning("Either artist or title or both were not found in the file's metadata.")

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Update genre metadata in MP3 files.")
    parser.add_argument("-p", "--path", type=str, help="Path to the MP3 file or directory containing MP3 files", required=True)
    args = parser.parse_args()

    # Set up Spotify API credentials using values from secrets.py
    client_id = secrets.CLIENT_ID
    client_secret = secrets.CLIENT_SECRET
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    expanded_path = os.path.expanduser(args.path)  # Expand user-provided path
    if os.path.isdir(expanded_path):
        for filename in os.listdir(expanded_path):
            if filename.endswith('.mp3'):
                file_path = os.path.join(expanded_path, filename)
                #logging.info('\n' + file_path)  
                logging.info(filename)
                
                process_file(sp, file_path)

    elif os.path.isfile(expanded_path) and expanded_path.endswith('.mp3'):
        process_file(sp, expanded_path)
    else:
        logging.error(f"The specified path does not exist or is not an MP3 file: {expanded_path}")

if __name__ == "__main__":
    main()