#!/bin/bash

# Read datasets base path from config
DATASETS_PATH=$(awk -F': ' '/^path:/ {print $2}' config.yaml | tr -d '"')
MATRIX_LIST_TXT=$(realpath "$DATASETS_PATH/matrices_list.txt")

INPUT_HTML="tmp.html"
OUTPUT_CSV="matrix_info.csv"
echo "Name,Group,MatrixID,NumRows,NumCols,Nonzeros,SparsityRatio,Link,ImageLink" > "$OUTPUT_CSV"

while IFS= read -r file; do
    prev_dir=$(basename "$(dirname "$file")")
    prev_prev_dir=$(basename "$(dirname "$(dirname "$file")")")

    if [[ $prev_dir == "Graph500" ]]; then
        echo "Skipping $file"
        continue
    fi

    group=$prev_prev_dir
    matrix=$(basename "$file" | sed -E 's/\.(mtx|bmtx)$//')
    file="$group/$matrix"

    echo "Fetching '$file' from SuiteSparse"
    link="https://sparse.tamu.edu/${file}"
    dwlcmd="wget ${link} -q -O - "
    ${dwlcmd} > ${INPUT_HTML}

    NAME=$(awk '/<th>Name<\/th>/,/<\/tr>/' "$INPUT_HTML" | sed -n 's/.*<td>\(.*\)<\/td>.*/\1/p')
    GROUP=$(awk '/<th>Group<\/th>/,/<\/tr>/' "$INPUT_HTML" | sed -n 's/.*<a[^>]*>\(.*\)<\/a>.*/\1/p')
    MATRIX_ID=$(awk '/<th>Matrix ID<\/th>/,/<\/tr>/' "$INPUT_HTML" | sed -n 's/.*<td>\(.*\)<\/td>.*/\1/p')
    NUM_ROWS=$(awk '/Num Rows/,/<\/tr>/' "$INPUT_HTML" | sed -n 's/.*<td>\(.*\)<\/td>.*/\1/p' | sed 's/,//g')
    NUM_COLS=$(awk '/Num Cols/,/<\/tr>/' "$INPUT_HTML" | sed -n 's/.*<td>\(.*\)<\/td>.*/\1/p' | sed 's/,//g')
    NONZEROS=$(awk '/Nonzeros/,/<\/tr>/' "$INPUT_HTML" | sed -n 's/.*<td>\(.*\)<\/td>.*/\1/p' | sed 's/,//g')
    IMAGE_LINK=$(awk '/carousel-item active/,/<\/div>/' "$INPUT_HTML" | sed -n 's/.*<a[^>]*href="\([^"]*\)".*/\1/p')
    SPR=$(echo "scale=10; $NONZEROS / ($NUM_ROWS * $NUM_COLS)" | bc -l)

    echo "$NAME,$GROUP,$MATRIX_ID,$NUM_ROWS,$NUM_COLS,$NONZEROS,$SPR,$link,$IMAGE_LINK" >> "$OUTPUT_CSV"
done < "${MATRIX_LIST_TXT}"

rm $INPUT_HTML
echo "CSV written to $OUTPUT_CSV"