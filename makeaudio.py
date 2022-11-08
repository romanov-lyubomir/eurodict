from gtts import gTTS
import pandas as pd
import os.path

words = pd.read_csv("static/data/temp.csv")
words = words.values.tolist()

for word in words:
    path = f"static/audio/{word[2]}.mp3"
    if not os.path.exists(path):
        file = gTTS(text=word[0], lang="de", slow=False)
        file.save(path)
        print(f"File {path} created for \"{word[0]}\"")


# file = gTTS(text="die Wade die Waden", lang="de", slow=False)
# file.save("static/audio/377.mp3")
