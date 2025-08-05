#copy to workdir
cp /var/www/offline-data/theBuddhasWords/mn/* ./
cp /var/www/offline-data/theBuddhasWords/dn/* ./
cp /var/www/offline-data/theBuddhasWords/sn/* ./
cp /var/www/offline-data/theBuddhasWords/an/* ./

cp /var/www/offline-data/theBuddhasWords/ud/* ./
cp /var/www/offline-data/theBuddhasWords/snp/* ./
cp /var/www/offline-data/theBuddhasWords/dhp/* ./
cp /var/www/offline-data/theBuddhasWords/it/* ./
cp /var/www/offline-data/theBuddhasWords/tha/* ./
cp /var/www/offline-data/theBuddhasWords/thi/* ./
  
#run scripts 
.venv/bin/python converter.py
.venv/bin/python add_titles.py
#.venv/bin/python scIndexes.py - when script will be ready


#organize all new files into folders
mkdir ud iti dhp snp thag thig kn
mv ud* ud/
mv it* iti/
mv dhp* dhp/
mv snp* snp/
mv tha* thag/
mv thi* thig/
mv ud iti dhp snp thag thig kn/

mkdir mn dn
mv mn* mn
mv dn* dn
mkdir an{1..11}
for i in an{1..11} ; do  mv ${i}.* $i/ ; done
mkdir sn{1..56}
for i in sn{1..56} ; do   mv ${i}.* $i/ ;  done
mkdir sn an
mv sn* sn/
mv an* an/

#move to real sutta folders
#
# rename translators to actual ones for MN, DN before or after moving
#
rm -rf ../../kn
mv kn ../../
rm -rf ../../sn
rm -rf ../../an
rm -rf ../../dn
rm -rf ../../mn
mv sn ../../
mv an ../../
mv dn ../../
mv mn ../../


exit 0

cd kn/iti
mv iti1-112_translation-en-bodhi.json  iti1-112_translation-en-thanissaro.json 
cd ../..


cd kn/dhp
for f in *bodhi*.json; do mv "$f" "${f//bodhi/buddharakkhita}"; done
cd ../..


cd kn/snp

cd ../..


cd kn/ud
for f in *bodhi*.json; do mv "$f" "${f//bodhi/anandajoti}"; done
cd ../..


cd kn/thag
for file in tha*; do
  new_name="thag${file:3}"
  mv "$file" "$new_name"
done
for f in *bodhi*.json; do mv "$f" "${f//bodhi/sujato+walton}"; done
cd ../..


cd kn/thig
for file in thi*; do
  new_name="thig${file:3}"
  mv "$file" "$new_name"
done
for f in *bodhi*.json; do mv "$f" "${f//bodhi/sujato+walton}"; done
cd ../..




#rename translators in DN and MN

# Bodhi
cd dn
mv dn1_translation-en-bodhi.json dn1_translation-en-bodhi.json
mv dn2_translation-en-bodhi.json dn2_translation-en-bodhi.json
mv dn15_translation-en-bodhi.json dn15_translation-en-bodhi.json

# Ānandajoti
mv dn16_translation-en-bodhi.json dn16_translation-en-anandajoti.json
mv dn20_translation-en-bodhi.json dn20_translation-en-anandajoti.json
mv dn32_translation-en-bodhi.json dn32_translation-en-anandajoti.json

# Kelly
mv dn31_translation-en-bodhi.json dn31_translation-en-kelly.json

# Walshe (все остальные из списка)
for f in dn{3..14} dn{17..19} dn{21..30} dn33 dn34; do
  mv "${f}_translation-en-bodhi.json" "${f}_translation-en-walshe.json"
done
cd ..

cd mn
for i in {1..152}; do
  echo mv "mn${i}_translation-en-bodhi.json" "mn${i}_translation-en-nyanamoli+bodhi.json"
done
cd ..





#not user subfolder structure
cd kn/snp
mkdir vagga{1..5}

for i in {1..5}
do
  mv snp${i}.* vagga${i} 
done
cd ../..



#find translator
grep "Translated from" *.html | sed -E 's/.*Translated from[^b]*by (.*)/\1/' | sort -ui