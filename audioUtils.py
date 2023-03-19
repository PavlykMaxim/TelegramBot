import moviepy.editor as mp
import os

class AudioExtractor():
    def audioExtractor(self, filename, user_id):
        if os.path.exists(f'data/users/{user_id}/audio'):
            pass
        else:
            os.mkdir(f'data/users/{user_id}/audio')

        new_filename = filename[:len(filename)-4]
        file_path = f'data/users/{user_id}/audio/{new_filename}_audio'

        video = mp.VideoFileClip(f'data/users/{user_id}/downloaded/{filename}')
        audio =  video.audio

        if audio.duration > 120:
            return None
        else:
            audio.write_audiofile(f'{file_path}.ogg')
            return True

