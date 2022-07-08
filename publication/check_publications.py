import argparse
import requests
# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.message import EmailMessage


class Publication_Check:
    epmc_rest_url_root = 'https://www.ebi.ac.uk/europepmc/webservices/rest'
    epmc_rest_url = f'{epmc_rest_url_root}/search'
    epmc_rest_url_2 = f'{epmc_rest_url_root}/article/PPR'

    pub2skip = ['PGP000058','PGP000077','PGP000238']

    def __init__(self, pgs_rest_url):
        self.pgs_rest_url = pgs_rest_url
        self.pub_count = 0
        self.pub_list = {}
        self.pub_updates_list = {}


    def rest_api_call(self, rest_url, parameters=None):
        if parameters:
            response = requests.get(rest_url, params=parameters)
        else:
            response = requests.get(rest_url)
        return response


    def rest_api_call_to_get_ppr(self, doi):
        '''
        Retrieve the PPR of the preprint via Europe PMC REST API, using the DOI
        Return the PPR if found
        '''
        ppr = None
        payload = {'format': 'json'}
        payload['query'] = 'doi:' + doi
        r = requests.get(self.epmc_rest_url, params=payload)
        r = r.json()
        if r['resultList']['result']:
            r = r['resultList']['result'][0]
            if r['pubType'] == 'preprint':
                ppr = r['id']
        return ppr


    def rest_api_call_to_epmc(self,ppr):
        '''
        REST API call to EuropePMC
        - query: the search query
        Return type: JSON
        '''
        payload = {'format': 'json', 'resultType': 'core'}
        result = self.rest_api_call(f'{self.epmc_rest_url_2}/{ppr}', payload)
        result = result.json()
        result = result['result']
        return result


    def fetch_pub_list(self):
        try:
            response = self.rest_api_call(self.pgs_rest_url)
            response_json = response.json()
            # Response with pagination
            if 'next' in response_json:
                count_items = response_json['count']
                results = response_json['results']
                # Loop over the pages
                while response_json['next'] and count_items > len(results):
                    response = self.rest_api_call(response_json['next'])
                    response_json = response.json()
                    results = results + response_json['results']
                if count_items != len(results):
                    print(f'The number of items are differents from expected: {len(results)} found instead of {count_items}')
            # Respone without pagination
            else:
                results = response_json
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            raise SystemExit(e)
        
        # Store relevant information
        for result in results:
            id = result['id']
            pmid = result['PMID']
            doi = result['doi']
            f_author = result['firstauthor']
            if not pmid and doi:
                self.pub_count += 1
                self.pub_list[id] = {'doi': doi, 'f_author': f_author}


    def check_pub_updates(self):
        for pgp_id in sorted(self.pub_list.keys()):
            if pgp_id not in self.pub2skip:
                doi = self.pub_list[pgp_id]['doi']
                ppr = self.rest_api_call_to_get_ppr(doi)
                if ppr:
                    result = self.rest_api_call_to_epmc(ppr)
                    if 'commentCorrectionList' in result:
                        if 'commentCorrection' in result['commentCorrectionList']:
                            self.pub_updates_list[pgp_id] = []
                            for correction in result['commentCorrectionList']['commentCorrection']:
                                id = correction['id']
                                source = correction['source']
                                reference = correction['reference'].replace('\n','').replace('     ',' ')
                                self.pub_updates_list[pgp_id].append(f'ID: {id} | Source: {source} | Ref: {reference}')



class PGS_Email():

    sender = 'auto@pgscatalog.org'
    title_prefix = 'PGS Publication checks - '

    def __init__(self, title, content, recipient):
        self.msg = EmailMessage()
        self.msg['Subject'] = self.title_prefix+title
        self.msg['From'] = self.sender
        self.msg['To'] = recipient
        self.msg.set_content(content)

    def send_message(self):
        s = smtplib.SMTP('localhost')
        s.send_message(self.msg)
        s.quit()




#############################################################

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--pgs_rest_url", help='PGS Catalog REST API URL to fetch the list of traits', required=True, metavar='REST_URL')
    argparser.add_argument("--recipient", help='Recipient of the email that will be sent', required=True, metavar='EMAIL')

    # Collect parameters
    args = argparser.parse_args()
    pgs_rest_url = args.pgs_rest_url
    recipient = args.recipient

    # Fetch information
    pub_check = Publication_Check(pgs_rest_url)
    pub_check.fetch_pub_list()
    pub_check.check_pub_updates()

    count_missing_pmid = len(pub_check.pub_list.keys())
    count_updates = len(pub_check.pub_updates_list.keys())

    # Generate email content
    title = ''
    content = f"Number of publications without PubMed ID: {count_missing_pmid}"
    if count_updates:
        title += f'{count_updates} updated publication(s)'
        content += '\n\nList of updated publication(s):\n'
        for pgp_id in pub_check.pub_updates_list:
            content += f"\n> Update(s) found for {pgp_id} ({pub_check.pub_list[pgp_id]['f_author']}):\n"
            for update in pub_check.pub_updates_list[pgp_id]:
                content += f"  - {update}\n"
    else:
        title = 'No updated publications available'
        content += '\n\nNo updates found/available'

    # Send results by email
    pgs_email = PGS_Email(title,content,recipient)
    pgs_email.send_message()

if __name__ == '__main__':
    main()