#!/usr/bin/python
import re
import string
import nltk
import codecs
import os
import struct
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

LIMIT = None                # (for testing) to limit the number of documents indexed
RECORD_TIME = False         # toggling for recording the time taken for indexer
BYTE_SIZE = 4               # docID is in int

"""
indexer which produces dictionary and postings file
params:
    document_directory: corpus directory for indexing
    dictionary_file:    dictionary of terms
    postings_file:      postings file for all terms in dictionary
"""



#runfile('D:/Documents/GitHub/boolean-retrieval-engine/index.py -i document_directory -d dictionary_file -p postings_file', wdir='D:/Documents/GitHub/boolean-retrieval-engine')

document_directory = 'D:/Documents/GitHub/boolean-retrieval-engine/documents'
dictionary_file = 'dictionary.txt'
postings_file = 'postings.txt'

#index(document_directory, dictionary_file, postings_file)


# preprocess docID list
docID_list = [int(docID_string) for docID_string in os.listdir(document_directory)]
docID_list.sort()

# create stemmer
stemFactory = StemmerFactory()
stemmer = stemFactory.create_stemmer()

docs_indexed = 0    # counter for the number of docs indexed
dictionary = {}     # key: term, value: [postings list]

# for each document in corpus
for docID in docID_list:
    if (LIMIT and docs_indexed == LIMIT): break
    file_path = os.path.join(document_directory, str(docID))

    # if valid document
    if (os.path.isfile(file_path)):
        file = codecs.open(file_path, encoding='utf-8')
        document = file.read().replace('\n', ' ') # read entire document

        # remove tags and lowercase text
        document = re.sub( r'\d+', '', document )
        document = re.sub( '<.*?>', ' ', document )
        document = document.translate(str.maketrans('', '', string.punctuation)).lower()

        #create stopword factory
        stopFactory = StopWordRemoverFactory()
        stopRemover = stopFactory.create_stop_word_remover()

        #remove stopword
        document = stopRemover.remove( document )

        #tokenization
        tokens = nltk.word_tokenize( document )   # list of word tokens from document

        # for each term in document
        for word in tokens:
            term = word
            term = stemmer.stem(term)   # stemming
            # if term not already in dictionary
            if (term not in dictionary):
                dictionary[term] = [docID]   # define new term in in dictionary
            # else if term is already in dictionary
            else:
                # if current docID is not yet in the postings list for term, append it
                if (dictionary[term][-1] != docID):
                    dictionary[term].append(docID)

        docs_indexed += 1
        file.close()

# open files for writing
dict_file = codecs.open(dictionary_file, 'w', encoding='utf-8')
post_file = open(postings_file, 'wb')

byte_offset = 0 # byte offset for pointers to postings file

# write list of docIDs indexed to first line of dictionary
dict_file.write('Indexed from docIDs:')
for i in range(docs_indexed):
    dict_file.write(str(docID_list[i]) + ',')
dict_file.write('\n')

# build dictionary file and postings file
for term, postings_list in dictionary.items():
    df = len(postings_list)                     # document frequency is the same as length of postings list

    # write each posting into postings file
    for docID in postings_list:
        posting = struct.pack('I', docID)   # pack docID into a byte array of size 4
        post_file.write(posting)

    # write to dictionary file and update byte offset
    dict_file.write(term + " " + str(df) + " " + str(byte_offset) + "\n")
    byte_offset += BYTE_SIZE * df

# close files
dict_file.close()
post_file.close()