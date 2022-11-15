import os.path

import pandas as pd
from gtts import gTTS

words = pd.read_csv("static/data/spanish/vocabulary/fruits.csv")
words = words.values.tolist()

for word in words:
    path = f"static/audio/spanish/vocabulary/{word[2]}.mp3"
    if not os.path.exists(path):
        file = gTTS(text=word[0], lang="es", slow=False)
        file.save(path)
        print(f"File {path} saved for audio: {word[0]}")
