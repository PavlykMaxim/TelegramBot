from pytube import YouTube
from pytube.exceptions import RegexMatchError

class VideoDownload():
    def video_dowloader(self, url, filename, user_id, mode):
        max_length = 60
        if mode == 'audio':
            max_length = 120

        try:
            yt = YouTube(url)
            if yt.length > max_length:
                return None

        except (RegexMatchError, AttributeError):
            return None

        else:
            print('Название видео: ', yt.title)
            stream = yt.streams.get_highest_resolution()

            if stream is not None:
                print("Скачиваем видео...")
                stream.download(output_path=f'data/users/{user_id}/downloaded', filename=filename)
                print("Видео успешно скачано!")
                return True
            else:
                print("Видео с таким разрешением не доступно для скачивания!")