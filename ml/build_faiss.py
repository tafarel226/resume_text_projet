from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json

model = SentenceTransformer('all-mpnet-base-v2')
# charge faq.csv ou sample
faq = [
    {'id':1, 'question':'Comment résumer un document?', 'answer_template':'Voici un résumé: {{}}'},
    {'id':2, 'question':'Où acheter X-Phone?', 'answer_template':'X-Phone est disponible à {{LOCATION}}.'},
]
texts = [f['question'] for f in faq]
emb = model.encode(texts, convert_to_numpy=True)
faiss.normalize_L2(emb)
index = faiss.IndexFlatIP(emb.shape[1])
index.add(emb)
faiss.write_index(index, './data/faiss.index')
with open('./data/faq_texts.json','w') as f:
    json.dump(faq,f)
print('Built faiss index')
