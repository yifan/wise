#!/usr/bin/env python

import os
import re
import codecs
import pycaption
import requests
import edit
from requests_toolbelt.streaming_iterator import StreamingIterator

def loadSrt(filename):
  fileid = os.path.basename(filename).split('.')[0]
  with codecs.open(filename, 'r', 'utf-8') as srtfile:
    content = srtfile.read()
    reader = pycaption.detect_format(content)
    if reader:
      caps = reader().read(content)
      return fileid, caps

def cleanText(line):
  line = re.sub(r'[.?,]', ' ', line.strip()) 
  line = re.sub(r'\[HES\]', ' ', line.strip()) 
  line = re.sub(r'\[UNK\]', ' ', line.strip()) 
  line = re.sub(r'\[MUSIC\]', ' ', line.strip()) 
  line = re.sub(r'\[NOISE\]', ' ', line.strip()) 
  line = re.sub(r'\[BREATH\]', ' ', line.strip()) 
  line = re.sub(r'\[APPLAUSE\]', ' ', line.strip()) 
  line = re.sub(r'\[FALSE ', ' ', line.strip()) 
  line = re.sub(r'\[INTER ', ' ', line.strip()) 
  line = re.sub(r'\[CORR ', ' ', line.strip())
  line = re.sub(r'\[NE:\w* ', ' ', line.strip())
  line = re.sub(r'\[FOR:AR ', ' ', line.strip())
  line = re.sub(r'\[REP.', ' ', line.strip())
  line = re.sub(r'\]', ' ', line.strip())
  line = re.sub(r' +', ' ', line.strip())
  return line

def isValid(line):
  if re.search('\[FOR', line):
    return False
  return True

def recognize(uri, wav):
  r = requests.post(uri, data=open(wav, 'rb'), headers={
    'Content-Type': 'audio/x-raw;+layout=(string)interleaved,+rate=(int)16000,+format=(string)S16LE,+channels=(int)1'
  })
  return r.json()

def main(args):
  srts = []
  for filename in args.files:
    fileid, caps = loadSrt(filename)
    for cap in caps.get_captions(caps.get_languages()[0]):
      text = cap.get_text()
      valid = isValid(text)
      text = cleanText(text)
      if not text:
        valid = False
      srts.append((valid, fileid, int(cap.start/1000), int(cap.end/1000), text))

  if args.wrd:
    words = set()
    for valid, _, _, _, text in srts:
      for word in text.split():
        words.update(word)

    dictionary = set()
    for line in codecs.open(args.wrd, 'r', 'utf-8'):
      for word in line.split():
        dictionary.update(word)

    nmissing = 0
    for word in words:
      if word not in dictionary:
        nmissing += 1

  if args.trn:
    textfile = codecs.open(os.path.join(args.trn, 'text'), 'w', 'utf-8')
    segments = open(os.path.join(args.trn, 'segments'), 'w')
    wavscp = open(os.path.join(args.trn, 'wav.scp'), 'w')
    utt2spk = open(os.path.join(args.trn, 'utt2spk'), 'w')
    spk2utt = open(os.path.join(args.trn, 'spk2utt'), 'w')
    for valid, fileid, start, end, text in srts:
      if valid:
        uttid = "{}_{:06d}_{:06d}".format(fileid, start, end)
        print("{} {}".format(uttid, text), file=textfile)
        print("{} {} {:.2f} {:.2f}".format(uttid, fileid, start/1000, end/1000), file=segments)
        print("{} {}".format(fileid, os.path.join(args.dir, fileid + ".wav")), file=wavscp)
        print("{} {}".format(fileid, fileid), file=utt2spk)
        print("{} {}".format(fileid, fileid), file=spk2utt)

  if args.wav:
    res = recognize(args.uri, args.wav)
    print(res)

  if args.rec:
    with codecs.open(args.rec, 'r', 'utf-8') as f:
      recs = []
      for line in f:
        recs.extend(line.split())

    refs = []
    for flag, fileid, start, end, text in srts:
      for token in text.split():
        refs.append((token, start, end, flag))

    def compare(hyp, ref):
      return ref[0].lower() == hyp.lower()

    def filterword(hyp, ref):
      return ref[-1]

    def filternone(hyp, ref):
      return True

    filterfunc = filterword if args.exclude_arabic else filternone

    scorer = edit.EditDistance(options={'compare': compare, 'filter': filterfunc})
    alignment = []
    wer = scorer.calculate(ref=refs, hyp=recs, alignment=alignment)
    if args.show_alignment:
      for ref, hyp in alignment:
        print(ref, hyp)
    print(scorer.detailed_result())


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='extract segment')
  parser.add_argument('--show-alignment', action='store_true', help='show alignment')
  parser.add_argument('--exclude-arabic', action='store_true', help='exclude arabic segments')
  parser.add_argument('--wrd', help='word list')
  parser.add_argument('--uri', default='http://asr.qcri.org/client/dynamic/recognize?lang=en', help='uri for asr server')
  parser.add_argument('--wav', help='wav file')
  parser.add_argument('--dir', help='directory to wav file')
  parser.add_argument('--trn', help='directory to store training files')
  parser.add_argument('--rec', help='recognition result text file')
  parser.add_argument('files', nargs='+', help='srt files')
  args = parser.parse_args()

  main(args)

