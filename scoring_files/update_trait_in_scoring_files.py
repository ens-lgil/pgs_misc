import os, re
import gzip
import argparse
import requests

file_extension = ".txt.gz"
rest_url = 'http://127.0.0.1:8000/rest/score/'
id_range = 99



def get_pgs_info(pgs_id):
    """"
    Generic method to perform REST API calls to the PGS Catalog
    > Parameters:
        - pgs_id: PGS ID
    > Return type: dictionary
    """
    rest_full_url = rest_url+pgs_id
    results = {'efos': set()}
    try:
        response = requests.get(rest_full_url)
        response_json = response.json()
        results['name'] = response_json['name']
        efos = response_json['trait_efo']
        for efo in efos:
            results['efos'].add((efo['id'],efo['label']))
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)
    return results



def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input_dir", help='Scoring files directory', required=True, metavar='INPUT_DIR')
    argparser.add_argument("--output_dir", help='Directory for the new scoring files', required=True, metavar='OUTPUT_DIR')
    argparser.add_argument("--files_gp_step", help='Select the hundred range, e.g. 200 => PGS IDs from 101 to 200', metavar='H_GRP_STEP')

    args = argparser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.isdir(input_dir):
        print("Directory '"+input_dir+"' can't be found")
        exit(1)

    if not os.path.isdir(output_dir):
        try:
            os.mkdir(output_dir, 0o755)
        except OSError:
            print (f'Creation of the output directory {output_dir} failed')
            exit(1)

    pgs_id_min = 0
    pgs_id_max = 0
    if args.files_gp_step:
        pgs_id_min = int(args.files_gp_step) - id_range
        pgs_id_max = int(args.files_gp_step)

    for scoring_file in os.listdir(input_dir):
        pgs_file_name = re.match('^PGS0+(\d+)'+file_extension+'$', scoring_file)
        
        if pgs_file_name:
            if pgs_id_min and pgs_id_max:
                pgs_id = int(pgs_file_name.group(1))
                if not pgs_id_min <= pgs_id <= pgs_id_max:
                    continue

            score_id = scoring_file.split(file_extension)[0]
            print(">>> Score ID: "+score_id)
            scoring_file_path = f'{input_dir}/{scoring_file}'

            with gzip.open(scoring_file_path, 'rb') as f_in:
                with gzip.open(f'{output_dir}/{scoring_file}', 'wb') as f_out:
                    pgs_info = get_pgs_info(score_id)
                    efos = pgs_info['efos']
                    print(f'\t- {efos}')
                    for f_line in f_in:
                        line = f_line.decode()
                        # Update header
                        if line.startswith('#'):
                            # Update EFO IDs in the header
                            if line.startswith('#trait_mapped'):
                                line = f'#trait_mapped={",".join([x[1] for x in efos])}\n'
                            elif line.startswith('#trait_efo'):
                                line = f'#trait_efo={",".join([x[0] for x in efos])}\n'
                        if '\r' in line:
                            line = line.replace('\r','\n')
                        elif not '\n' in line :
                            line += '\n'

                        f_out.write(line.encode())


if __name__ == '__main__':
    main()
