import os.path

import pandas as pd
from gtts import gTTS

tenses = ["praesens", "praeteritum", "perfekt", "plusquamperfekt", "futur_eins", "futur_zwei"]
index = 0
verbs = ["sein", "haben"]

for tense in tenses:
    for verb in verbs:
        if tense == "praesens":
            index = 1
        elif tense == "praeteritum":
            index = 2
        elif tense == "perfekt":
            index = 3
        elif tense == "plusquamperfekt":
            index = 4
        elif tense == "futur_eins":
            index = 5
        elif tense == "futur_zwei":
            index = 6
        words = pd.read_csv(f"static/data/german/verbs/{verb}.csv")
        words = words.values.tolist()
        for word in words:
            path = f"static/audio/german/sentences/{tense}/{verb}/{word[7]}.mp3"
            if not os.path.exists(path) or True:
                file = gTTS(text=f"{word[0]} {word[index]}", lang="de", slow=False)
                file.save(path)
                print(f"Saved {word[0]} {word[index]}")