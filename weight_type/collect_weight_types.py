import os, re
# import gzip
import argparse
import pandas as pd

file_extension = ".txt.gz"

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input_dir", help='Scoring files directory', required=True, metavar='INPUT_DIR')
    argparser.add_argument("--output_file", help='Output file', required=True, metavar='OUTPUT_FILE')

    args = argparser.parse_args()

    input_dir = args.input_dir
    output_file = args.output_file

    if not os.path.isdir(input_dir):
        print("Directory '"+input_dir+"' can't be found")
        exit(1)


    count_scores = 0
    count_weight = 0
    count_mixed_weight = []
    score_weight_type = {}

    for scoring_file in sorted(os.listdir(input_dir)):
        if re.match('^PGS\d+'+file_extension+'$', scoring_file):
            score_id = scoring_file.split(file_extension)[0]
            # print(">>> Score ID: "+score_id)
            scoring_file_path = f'{input_dir}/{scoring_file}'

            df_scoring = pd.read_table(scoring_file_path, dtype='str', engine = 'python', comment='#')
            # print(f'- {score_id} => {df_scoring.memory_usage(deep=True).sum()}')
            count_scores += 1

            weight_type = 'NR'

            if 'weight_type' in df_scoring.columns:
                count_weight += 1
                weight_types_list = set(df_scoring['weight_type'])
                if len(weight_types_list) > 1:
                    count_mixed_weight.append(score_id)
                weight_type = ','.join(weight_types_list)

            score_weight_type[score_id] = weight_type
            

    out = open(output_file,'w')
    for pgs_id in sorted(score_weight_type.keys()):
        out.write(f'{pgs_id}\t{score_weight_type[pgs_id]}\n')
    out.close()

    print(f'Scoring files - total: {count_scores}')
    print(f'Scoring files - weight_type : {count_weight}')
    print(f'Scoring files - mixed weight_type : {len(count_mixed_weight)}')
    print(','.join(count_mixed_weight))


if __name__ == '__main__':
    main()
