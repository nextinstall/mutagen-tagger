# mutagen-tagger - MP3 Metadata Updater

## Overview
This script is designed to enhance the metadata of MP3 files, specifically focusing on updating genre information and comments by utilizing the Spotify API. It reads MP3 files, extracts their metadata, searches for the track on Spotify to determine the genre, and updates the MP3 file's metadata accordingly.

## Requirements
- Python 3.x
- Mutagen
- Spotipy
- A Spotify Developer account to access the Spotify Web API (for Client ID and Client Secret)

## Installation

Before running the script, ensure you have Python installed on your system. Then, install the required Python packages using pip:

`pip install mutagen spotipy`

OR

`pip install -r requirements.txt`




## Configuration

1. Create a Spotify Developer account and register an application to obtain the `Client_ID` and `Client_Secret`.
2. Store these credentials in a `secrets.py` file in the same directory as the script with variables `CLIENT_ID` and `CLIENT_SECRET`.

## Usage

python mp3_metadata_updater.py -p <path to MP3 file or directory>


- `<path to MP3 file or directory>`: Specify the path to an MP3 file or a directory containing MP3 files. The script updates the genre and comments metadata for each MP3 file found.


## Features

- **Metadata Extraction**: Extracts existing metadata from MP3 files, including artist, title, comments, and genre.
- **Spotify Genre Search**: Searches Spotify for the track by artist and title to retrieve the genre.
- **Metadata Update**: Updates the MP3 file's genre and comments section with new information retrieved from Spotify.
- **Logging**: Provides detailed logging for actions performed and any errors encountered.

## Handling Rate Limiting
The script includes handling for Spotify's rate limiting. If rate limiting is encountered, the script will pause execution for the specified time before retrying.

## Error Handling
Errors encountered during execution, such as issues with Spotify API calls or reading/writing MP3 metadata, are logged for troubleshooting.

## Limitations
- The script currently only updates the first genre retrieved from Spotify.

## Contributing
Contributions to improve the script, add new features, or fix bugs are welcome. Please submit a pull request or open an issue on the project's repository.

## License
GPL v3