import os.path

import pandas as pd
from gtts import gTTS

words = pd.read_csv("transport.csv")
words = words.values.tolist()

for word in words:
    path = f"static/audio/german/vocabulary/{word[2]}.mp3"
    if not os.path.exists(path):
        file = gTTS(text=word[0], lang="de", slow=False)
        file.save(path)
        print(f"File {path} saved for audio: {word[0]}")
