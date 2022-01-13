import requests
import argparse


def rest_api_call_to_epmc(query):
        '''
        REST API call to EuropePMC
        - query: the search query
        Return type: JSON
        '''
        payload = {'format': 'json'}
        payload['query'] = query
        result = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
        result = result.json()
        result = result['resultList']['result'][0]
        return result


def get_publication_information(pmid):
        '''
        Retrieve the main publication information from EuropePMC (via their REST API),
        using the DOI or the PubMed ID.
        '''
        result = rest_api_call_to_epmc(f'ext_id:{pmid}')

        if result:
            firstauthor = result['authorString'].split(',')[0]
            authors = result['authorString']
            title = result['title']
            date_publication = result['firstPublicationDate']
            print(f"\n# firstauthor:\n{firstauthor}")
            print(f"\n# authors:\n{authors}")
            print(f"\n# title:\n{title}")
            print(f"\n# date_publication:\n{date_publication}")
            if result['pubType'] == 'preprint':
                journal = result['bookOrReportDetails']['publisher']
            else:
                journal = result['journalTitle']
            print(f"\n# journal:\n{journal}")

            print(f"\n# SQL update:\nUPDATE catalog_publication SET \"PMID\"={pmid}, firstauthor='{firstauthor}', authors='{authors}', title='{title}', date_publication='{date_publication}', journal='{journal}' WHERE id='';\n")

        else:
            print(f'Can\'t find a result on EuropePMC for the publication: {pmid}')


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--pmid", help='PubMed ID', required=True, metavar='PMID')

    args = argparser.parse_args()

    pmid = args.pmid
    print(f'PMID: {pmid}')
    get_publication_information(pmid)


if __name__ == '__main__':
    main()
