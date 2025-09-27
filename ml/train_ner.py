# Ce script illustre l'entraînement spaCy; adaptez les datasets
import spacy
from spacy.util import minibatch, compounding
import random

TRAIN_DATA = [
    ("Le produit X-Phone est disponible à Paris", {"entities": [(12,19,"PRODUCT"),(37,42,"LOCATION")] }),
]

nlp = spacy.blank("fr")
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

for _, annotations in TRAIN_DATA:
    for ent in annotations.get('entities'):
        ner.add_label(ent[2])

optimizer = nlp.begin_training()
for itn in range(30):
    random.shuffle(TRAIN_DATA)
    losses = {}
    batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.5))
    for batch in batches:
        texts, annotations = zip(*batch)
        nlp.update(texts, annotations, sgd=optimizer, drop=0.3, losses=losses)
    print('Losses', losses)

nlp.to_disk('./data/ner_model')
print('Saved model to ./data/ner_model')
