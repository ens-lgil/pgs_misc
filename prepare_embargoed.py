import requests
import argparse


def rest_api_call(query,type,curation_url):
        '''
        REST API call
        - query: the searched ID
        - type: the type of data (e.g. score, publication, ...)
        - curation_url: URL of the Curation website
        Return type: JSON
        '''
        payload = {'format': 'json'}
        result = requests.get(curation_url+'/rest/'+type+'/'+query, params=payload)
        result = result.json()
        return result

def rest_api_call_publication(query,curation_url):
        '''
        REST API call
        - query: the Publication ID
        - curation_url: URL of the Curation website
        Return type: JSON
        '''
        result = rest_api_call(query,'publication',curation_url)
        return result

def rest_api_call_score(query,curation_url):
        '''
        REST API call
        - query: the Score ID
        - curation_url: URL of the Curation website
        Return type: JSON
        '''
        result = rest_api_call(query,'score',curation_url)
        return result


def get_publication_information(pgp_id,curation_url):
        '''
        Retrieve the main publication information from EuropePMC (via their REST API),
        using the DOI or the PubMed ID.
        - pgp_id: the PGS Publication ID (e.g. PGP000001)
        - curation_url: URL of the Curation website
        '''
        scores = []
        firstauthor = ''

        result = rest_api_call_publication(pgp_id,curation_url)
        if result:
            scores = result['associated_pgs_ids']['development']
            firstauthor = result['firstauthor']
            title = result['title']
            sql_title_col = ''
            sql_title_val = ''
            if title != '':
                sql_title_col = ',title'
                sql_title_val = f",'{title}'"
            sql_pub = f"INSERT INTO catalog_embargoedpublication (id,firstauthor{sql_title_col}) VALUES ('{pgp_id}','{firstauthor}'{sql_title_val});"
            print(f"> SQL PUB:\n{sql_pub}\n")

        if scores:
            for score in scores:
                score_result = rest_api_call_score(score,curation_url)
                if score_result:
                    sql_score = f"INSERT INTO catalog_embargoedscore (id,firstauthor,name,trait_reported) VALUES ('{score}','{firstauthor}','{score_result['name']}','{score_result['trait_reported']}');"
                    print(f"> SQL SCORE:\n{sql_score}")



def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--pgp", help='Publication ID (PGP ID)', required=True, metavar='PGP_ID')
    argparser.add_argument("--server", help='Curation server URL (i.e. the Curation URL)', required=True, metavar='URL')

    args = argparser.parse_args()

    pgp_id = args.pgp
    server = args.server
    print(f'# PGP ID: {pgp_id}')
    get_publication_information(pgp_id,server)


if __name__ == '__main__':
    main()