# spotify_utils.py

from app.spotify_api import get_track_features, get_related_artists


def process_top_tracks(data, access_token):
    top_tracks = {}
    num_tracks = 1

    for datum in data.get("items", []):
        track_id = datum.get("id")
        if not track_id:
            continue  # Skip if track ID is missing

        # Get audio features for the track
        try:
            features = get_track_features(access_token, track_id)
        except Exception as e:
            print(f"Error fetching audio features for track {datum.get('name')}: {e}")
            features = {}

        artists = []
        for artist in datum.get("artists", []):
            artists.append({
                "name": artist.get("name", "Unknown Artist"),
                "artist_link": artist.get("href", "#")
            })

        top_tracks[num_tracks] = {
            "track_name": datum.get("name", "Unknown Track"),
            "mp3_preview_url": datum.get("preview_url"),
            "track_url": datum.get("external_urls", {}).get("spotify", "#"),
            "duration_ms": datum.get("duration_ms", 0),
            "artists": artists,
            "album_name": datum.get("album", {}).get("name", "Unknown Album"),
            "album_link": datum.get("album", {}).get("external_urls", {}).get("spotify", "#"),
            "album_image": datum.get("album", {}).get("images", [{}])[0].get("url", ""),
            "release_date": datum.get("album", {}).get("release_date", "Unknown Date"),
            "popularity": datum.get("popularity", 0),
            "valence": features.get("valence"),
            "danceability": features.get("danceability"),
        }
        num_tracks += 1

    return top_tracks


def process_top_artists(data, access_token, related_limit=5):
    top_artists = {}
    num_artists = 1

    for artist_data in data.get("items", []):
        artist_id = artist_data.get("id")
        if not artist_id:
            continue  # Skip if artist ID is missing

        # Fetch related artists
        try:
            related_artists = get_related_artists(access_token, artist_id, limit=related_limit)
        except Exception as e:
            print(f"Error fetching related artists for {artist_data.get('name')}: {e}")
            related_artists = []

        top_artists[num_artists] = {
            "name": artist_data.get("name", "Unknown Artist"),
            "artist_url": artist_data.get("external_urls", {}).get("spotify", "#"),
            "genres": ", ".join(artist_data.get("genres", [])),
            "image_url": artist_data.get("images", [{}])[0].get("url", ""),
            "popularity": artist_data.get("popularity", 0),
            "followers": artist_data.get("followers", {}).get("total", 0),
            "related_artists": related_artists,
        }
        num_artists += 1

    return top_artists
