input_dir=$1

word_from=''
word_to=''

# declare -a ids_list=("PGS000832" "PGS000833" "PGS000834") 
declare -a ids_list=() 

for pgs_id in "${ids_list[@]}"
do
    filepath="$input_dir/$pgs_id.txt"
    gz_filepath="$filepath.gz"
    if [[ -f "$gz_filepath" ]]; then
        echo "- $pgs_id"
        gunzip $gz_filepath
        if grep -q "$word_from" $filepath; then
            # Replace word
            sed -i '' "s/$word_from/$word_to/g" $filepath
            # Remove trailing new line
            perl -pi -e 'chomp if eof' $filepath
            echo "  >> '$word_from' replaced by '$word_to'!"
        else
            echo "  >> '$word_from' not found!"
        fi
        gzip $filepath
    else
         echo "- $pgs_id: '$filepath' doesn't exists!"
    fi
done