import os.path

import pandas as pd
from gtts import gTTS

tenses = ["presente", "futuro"]
index = 0
verbs = ["ser", "estar", "haber"]

for tense in tenses:
    for verb in verbs:
        if tense == "presente":
            index = 1
        elif tense == "futuro":
            index = 2
        words = pd.read_csv(f"static/data/spanish/verbs/{verb}.csv")
        words = words.values.tolist()
        for word in words:
            path = f"static/audio/spanish/sentences/{tense}/{verb}/{word[3]}.mp3"
            if not os.path.exists(path) or True:
                file = gTTS(text=f"{word[0]} {word[index]}", lang="es", slow=False)
                file.save(path)
                print(f"Saved {word[0]} {word[index]} under {path}")