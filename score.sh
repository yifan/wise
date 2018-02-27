#!/bin/bash

for FILENAME in *.txt; do
  BASENAME=$(basename $FILENAME .txt)
   echo $BASENAME
  #pipenv run python scripts/score.py --show-alignment clean/En/Srt/$BASENAME.wav.srt $FILENAME | tee $FILENAME.align
  #pipenv run python scripts/extract.py --show-alignment --rec $FILENAME clean/En/Srt/$BASENAME.wav.srt  | tee $FILENAME.align2
  pipenv run python scripts/extract.py --exclude-arabic --rec $FILENAME clean/En/Srt/$BASENAME.wav.srt
done | sed 's:,: :g' | awk '\
  BEGIN{nerr=0;nwrd=0;nins=0;ndel=0;nsub=0;} \
  NR%2==0{nerr+=$5;nwrd+=$7;nins+=$8; ndel+=$10; nsub+=$12; print $0;} \
  NR%2==1{print $0;} \
  END{print(nerr/nwrd, nins, ndel, nsub);}'
