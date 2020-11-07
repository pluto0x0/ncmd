for i in *.ui; do
	pyuic5 -o ${i%%.*}.py ${i}
	echo $i;
done