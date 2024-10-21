def process_top_tracks(data):
    top_tracks = {}
    num_tracks = 1

    for datum in data["items"]:
        artists = []
        for artist in datum["artists"]:
            artists.append({
                "name": artist["name"],
                "artist_link": artist["href"]
            })

        top_tracks[num_tracks] = {
            "track_name": datum["name"],
            "mp3_preview_url": datum["preview_url"],
            "track_url": datum["external_urls"]["spotify"],
            "duration_ms": datum["duration_ms"],
            "artists": artists,
            "album_name": datum["album"]["name"],
            "album_link": datum["album"]["external_urls"]["spotify"],
            "album_image": datum["album"]["images"][0]["url"],
            "release_date": datum["album"]["release_date"],
        }
        num_tracks += 1

    return top_tracks

def process_top_artists(data):
    top_artists = {}
    num_artists = 1

    for artist_data in data["items"]:
        top_artists[num_artists] = {
            "name": artist_data["name"],
            "artist_url": artist_data["external_urls"]["spotify"],
            "genres": ", ".join(artist_data.get("genres", [])),
            "image_url": artist_data["images"][0]["url"] if artist_data["images"] else "",
        }
        num_artists += 1

    return top_artists

