import os
import json

os.chdir(os.path.dirname(__file__))

file_ = "french_bw"

with open (f"{file_}.txt", 'r') as f:
    txt_bw = f.read()

txt_bw = txt_bw.splitlines()
txt_bw = [i.lower() for i in txt_bw]

two_words = [(i.split(" "), n) for n, i in enumerate(txt_bw) if len(i.split(" ")) > 1]
two_words_trie = [(' '.join([a for a in i[0] if a not in txt_bw]), i[1]) for i in two_words]

for n, del_ in enumerate(two_words_trie):
    txt_bw.pop(del_[1]-n)

replacement = (',', '.', '?', '!', '/', ':', ';', '||', '|', '@', '0', "'", '%', '*', '+', '$', '1', '3', '5', '2', '4', '6', '7', '8', '9')

for r in replacement:
    txt_bw = [i for i in txt_bw if r not in i]

accent = (['é', 'e'],
          ['è', 'e'],
          ['ê', 'e'],
          ['à', 'a'],
          ['â', 'a'],
          ['û', 'u'],
          ['ù', 'u'],
          ['î', 'i'],
          ['ô', 'o'])

for e in accent:
    txt_bw.extend([i.replace(e[0], e[1]) for i in txt_bw if e[0] in i])
    

with open(f"../../{file_}.json", "w") as f:
    json.dump(txt_bw, f, indent=4)

print("ALL DONE. SUCCESS")