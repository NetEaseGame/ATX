
for name in *.py
do
	echo "NAME: $name"
	pylint "$name"
done
