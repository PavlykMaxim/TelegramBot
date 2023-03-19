import cv2
from moviepy.editor import *
import os

class VideoCropper():
    def cropping(self, filename, user_id):
        if os.path.exists(f'data/users/{user_id}/cropped'):
            pass
        else:
            os.mkdir(f'data/users/{user_id}/cropped')
        cap = cv2.VideoCapture(f'data/users/{user_id}/downloaded/{filename}')

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        center_x = int(width / 2)
        center_y = int(height / 2)

        frame_size = min(width, height)
        frame_width = int(frame_size)
        frame_height = int(frame_size)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        new_filename = filename[:len(filename)-4]
        out = cv2.VideoWriter(f'data/users/{user_id}/cropped/{new_filename}_cropped.mp4', fourcc, fps, (frame_width, frame_height))

        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            
            if ret:
                frame = frame[(center_y - frame_height // 2):(center_y + frame_height // 2), (center_x - frame_width // 2):(center_x + frame_width // 2)]
                frame = cv2.resize(frame, (400, 400))
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(rgb_frame)
                out.write(rgb_frame)
            else:
                break
        
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        video_clip = ImageSequenceClip(frames, fps=fps)

        audio_clip = AudioFileClip(f'data/users/{user_id}/downloaded/{filename}')

        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(f'data/users/{user_id}/cropped/{new_filename}_final.mp4', fps=fps)

        os.remove(f'data/users/{user_id}/cropped/{new_filename}_cropped.mp4')
