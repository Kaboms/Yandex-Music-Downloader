import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from yandex_music import ClientAsync
from yandex_music import Track
import re
import music_tag
import json

def download_track(track : Track, conf):
    artist = re.sub(r'[\<\>\:\"\/\\\|\?\*]', '', track.artists_name()[0])
    trackName = str(f"{track.title}.mp3")
    trackName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', '', trackName)

    downloadPath = ""
    if conf['createFolders']:
        artistPath = os.path.join(conf['downloadPath'], artist)
        if not os.path.exists(artistPath):
            os.makedirs(artistPath)

        downloadPath = os.path.join(artistPath, trackName)
    else:
        downloadPath = os.path.join(conf['downloadPath'], trackName)

    if not os.path.exists(downloadPath):
        print(downloadPath)
        try:
            asyncio.run(track.download_async(downloadPath, 'mp3'))
            if conf['fillMetaData']:
                audiofile = music_tag.load_file(downloadPath)
                audiofile['artist'] = artist
                audiofile['albumartist'] = artist
                audiofile['album'] = track.albums[0].title
                cover = asyncio.run(track.download_cover_bytes_async())
                audiofile['artwork'] = cover
                audiofile.save()
        except Exception as ex:
            print("Failed to download " + downloadPath + " " + ex)

async def main():
    confFile = open('conf.json')
    conf = json.load(confFile)
    client = ClientAsync(conf['token'])

    await client.init()
    tracks = await client.users_likes_tracks()
    tracks = await tracks.fetch_tracks_async()
    print(f"Liked tracks: {len(tracks)}")

    print("Get playlists")

    playlists = await client.users_playlists_list()
    for playlist in playlists:
        shortTracks = await playlist.fetch_tracks_async()
        tracks_ids = []
        for track in shortTracks:
            tracks_ids.append(track.id)

        playlist_tracks = await client.tracks(tracks_ids)
        tracks.extend(playlist_tracks)

        print(f"Playlist \"{playlist.title}\" with {len(playlist_tracks)} tracks" )

    print(f"Total tracks: {len(tracks)}")

    with ThreadPoolExecutor(max_workers=conf['workersAmount']) as executor:
        for track in tracks:
            executor.submit(download_track, track, conf)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())