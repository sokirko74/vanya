from pytube import YouTube


def main():
    YouTube('https://youtube.com/watch?v=TLYtw7FBfzQ').streams.first().download()

    # yt = YouTube('http://youtube.com/watch?v=2lAe1cqCOXo')
    # (yt.streams
    #  .filter(progressive=True, file_extension='mp4'))
    #  .order_by('resolution')
    #  .desc()
    #  .first()
    #  .download())


if __name__ == "__main__":
    main()