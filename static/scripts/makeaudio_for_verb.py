import os.path

import pandas as pd
from gtts import gTTS

tense = "futuro_semplice"
verbs = ["avere", "capire", "dare", "dire", "dormire", "dovere", "essere", "fare", "finire", "leggere", "parlare", "potere",
"sapere", "stare", "trovare", "uscire", "vedere", "venire", 'volere']

for verb in verbs:
    if verb == "avere":
        words = pd.read_csv(f"static/data/verbs/{verb}.csv")
        words = words.values.tolist()
        for word in words:
            path = f"static/audio/sentences/{tense}/{verb}/{word[3]}.mp3"
            if not os.path.exists(path):
                file = gTTS(text=f"{word[0]} {word[2]}", lang="it", slow=False)
                file.save(path)


# file = gTTS(text="la bistecca", lang="it", slow=False)
# file.save("static/audio/38.mp3")
