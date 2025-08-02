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


mkdir ud iti dhp snp thag thig kn
mv ud* ud/
mv iti* iti/
mv dhp* dhp/
mv snp* snp/
mv thag* thag/
mv thi* thig/
mv ud iti dhp snp thag thig kn/


rm -rf ../../kn

rm -rf ../../sn
rm -rf ../../an
rm -rf ../../dn
rm -rf ../../mn
mv sn ../../
mv an ../../
mv dn ../../
mv mn ../../
mv kn ../../
