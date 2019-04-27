import pylast
import configparser
import logging
import time
import argparse
import os
import errno
import pandas as pd
from tqdm import tqdm

logger = logging.getLogger()
temps_debut = time.time()


def main():
    args = parse_args()
    file = args.file
    artist = args.artist
    if not file and not artist:
        logger.error("Use the -f/--file or the -a/--artist flags to input one or several artists to search")
        exit()

    config = configparser.ConfigParser()
    config.read('config.ini')
    API_KEY = config['lastfm']['API_KEY']
    API_SECRET = config['lastfm']['API_SECRET']
    username = config['lastfm']['username']
    password = pylast.md5(config['lastfm']['password'])

    network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET,
                                   username=username, password_hash=password)

    if artist:
        artists = artist.split(',')
    else:
        df = pd.read_csv(file, sep='\t', encoding='utf-8')
        df.columns = ['Artist', 'Album', 'Track', 'Date', 'Timestamp']
        logger.debug(df.columns)
        artists = df.Artist.unique()
    n_artists = len(artists)
    logger.debug(f"Number of artists : {n_artists}")

    dict_artists = {}
    for index, artist in tqdm(enumerate(artists), total=n_artists):
        logger.debug(f"{index}: {artist}")
        dict = {}
        a = network.get_artist(artist)
        dict['Name'] = a.get_name()
        dict['URL'] = a.get_url()
        dict['Listeners'] = a.get_listener_count()
        dict['Playcount'] = a.get_playcount()

        tags = a.get_top_tags(20)
        for i, t in enumerate(tags):
            dict[f"Tag {i}"] = t.item.name
            dict[f"Weight tag {i}"] = t.weight

        tracks = a.get_top_tracks(10)
        for i, t in enumerate(tracks):
            dict[f"Top track {i}"] = t.item.title
            dict[f"Weight top track {i}"] = t.weight

        albums = a.get_top_albums(10)
        for i, t in enumerate(albums):
            dict[f"Top album {i}"] = t.item.title
            dict[f"Weight top album {i}"] = t.weight

        similar = a.get_similar(50)
        for i, t in enumerate(similar):
            dict[f"Similar artist {i}"] = t.item.name
            dict[f"Match similar artist {i}"] = t.match
        try:
            os.makedirs('Exports/Artists/')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        dict_artists[index] = dict

        df_export = pd.DataFrame.from_dict(dict, orient='index')
        df_export.to_csv(f"Exports/Artists/{artist}_information.csv", sep='\t')

    df_export_all = pd.DataFrame.from_dict(dict_artists, orient='index')
    df_export_all.to_csv(f"Exports/artists_information.csv", sep='\t')
    # with open(f"Exports/artists_information.csv", 'w') as f:
    #     f.write(f"Artist\tAlbum\tTitle\tDate\tTimestamp\n")
    #     logger.debug("Exporting timeline")
    #     for title in tqdm(tracks):
    #         title_line = f"{title.track.artist}\t{title.album}\t{title.track.title}\t{title.playback_date}\t{title.timestamp}\n"
    #         f.write(title_line)

    logger.info("Runtime : %.2f seconds" % (time.time() - temps_debut))


def parse_args():
    parser = argparse.ArgumentParser(description='Python skeleton')
    parser.add_argument('--debug', help="Display debugging information", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    parser.add_argument('-f', '--file', help='File containing the timeline', type=str)
    parser.add_argument('-a', '--artist', help='Artists (separated by comma)', type=str)
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    return args


if __name__ == '__main__':
    main()
