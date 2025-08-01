
mkdir html trn root
mv *root* root/ ; mv *translat* trn/ ; mv *html* html/

for d in html trn root
do 
cd $d
mkdir sn{1..56}
for i in sn{1..56} ; do  mv ${i}.* $i/ ; done
cd ..
done
