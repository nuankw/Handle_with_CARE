import os
from os import listdir
from pathlib import Path
from tqdm import tqdm

import re
import string
import json

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer

import math
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from lingua import LanguageDetectorBuilder, Language
import pke

from markdown import Markdown
from io import StringIO

detokenizer = TreebankWordDetokenizer()
stop_words = set(stopwords.words('english'))
vectorizer = TfidfVectorizer()
lang_detector = LanguageDetectorBuilder.from_all_languages().build()
MultipartiteRank_extractor = pke.unsupervised.MultipartiteRank()

def pretty_print(data):
    print(json.dumps(data, indent=4))
    
def read_jsonl(path):
    with open(path, "r") as f:
        lines = f.readlines()
        return [json.loads(line) for line in lines]
    
def read_jsonl_as_dict_with_subm_ids_as_keys(path):
    id_2_obj = {}
    with open(path, "r") as f:
        for line in f.readlines():
            obj = json.loads(line)
            if "id" in obj:
                id_2_obj[obj["id"]] = obj
            else:
                id_2_obj[obj["submission_id"]] = obj
    return id_2_obj

def write_jsonl(path, data):
    with open(path, "w") as f:
        for line in data:
            f.write(json.dumps(line) + "\n")

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)

def get_sorted_json_fps_from(dirpath):
    fps = sorted([os.path.join(dirpath,f) for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f)) and f.endswith(".json")])
    return fps

def get_sorted_jsonl_fps_from(dirpath):
    fps = sorted([os.path.join(dirpath,f) for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f)) and f.endswith(".jsonl")])
    return fps

def get_sorted_dates_from_fps(fps):
    return sorted([re.findall(r"\d{4}-\d{2}-\d{2}", fp)[0] for fp in fps])

def get_sorted_jsonl_files_of_given_dates_from(dirpath, dates):
    fps = get_sorted_jsonl_fps_from(dirpath)
    fps = [fp for fp in fps if re.findall(r"\d{4}-\d{2}-\d{2}", fp)[0] in dates]
    return fps

def get_langs_set(text):
    scores = lang_detector.compute_language_confidence_values(text)
    langs = set([score.language.name for score in scores if score.value > 0.8])
    return langs

def get_content_words(sent):
    sent = sent.translate(str.maketrans('', '', string.punctuation))
    word_tokens = word_tokenize(sent)
    content_words = [w for w in word_tokens if not w.lower() in stop_words]
    return content_words

def get_tfidf_vecs(sentences):
    return vectorizer.fit_transform(sentences).toarray()

def compute_similarity(sentences, token_method=get_tfidf_vecs, distance_func=cosine_similarity):
    vecs = token_method(sentences)
    return distance_func(vecs)

def get_MultipartiteRank_keyphrases(doc):
    MultipartiteRank_extractor.load_document(input=doc,language='en',stoplist=stop_words)
    pos = {'NOUN', 'PROPN', 'ADJ'}
    MultipartiteRank_extractor.candidate_selection(pos=pos)
    MultipartiteRank_extractor.candidate_weighting(alpha=1.1,threshold=0.74,method='average')
    return MultipartiteRank_extractor.get_n_best(n=10)

# https://stackoverflow.com/questions/761824/python-how-to-convert-markdown-formatted-text-to-text
def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()

# patching Markdown
Markdown.output_formats["plain"] = unmark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False

def unmark(text, markdown_object=__md):
    return markdown_object.convert(text)

def get_cleaned_text(text):
    # https://stackoverflow.com/questions/11331982/how-to-remove-any-url-within-a-string-in-python/40823105#comment117731306_40823105
    text = re.sub(r"\S*https?:\S*", "", text)
    text = re.sub(r"\S*http?:\S*", "", text)
    text = unmark(text)
    return text