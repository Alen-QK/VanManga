import base64

from utils.make_path import path_exists_make


def saveThumbnail(manga_object):
    manga_id, thumbnail = manga_object["manga_id"], manga_object["thumbnail"]
    path_exists_make('/vanmanga/thumbnails')
    thumbnail_path = f'/vanmanga/thumbnails/{manga_id}.jpg'
    # path_exists_make('../thumbnails')
    # thumbnail_path = f'../thumbnails/{manga_id}.jpg'

    with open(thumbnail_path, 'wb') as f:
        f.write(base64.b64decode(thumbnail))

    return f'{manga_id}.jpg'