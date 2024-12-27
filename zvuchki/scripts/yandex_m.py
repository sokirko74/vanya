from yandex_music import Client


def main():
    client = Client('y0_AgAAAAAADK-pAAG8XgAAAADuYXiPzgDIBIh8RvW6nkDAYcNnzefweJ4')
    client.init()
    #client.users_likes_tracks()[0].fetch_track().download('example.mp3')
    client.artists_tracks(4331744).tracks[0].download('example.mp3')


if __name__ == "__main__":
    main()
