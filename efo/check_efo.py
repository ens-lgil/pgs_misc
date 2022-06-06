import argparse
import requests
# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.message import EmailMessage


class EFO_Check:

    ols_rest_url = 'https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id='

    def __init__(self, pgs_rest_url):
        self.pgs_rest_url = pgs_rest_url
        self.efo_count = 0
        self.efo_list = {}
        self.efo_issue = {
            'obsolete': [],
            'missing': []
        }

    def rest_api_call(self, rest_url):
        response = requests.get(rest_url)
        return response


    def fetch_efo_list(self):
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
        
        self.efo_count = len(results)
        for result in results:
            trait_id = result['id']
            trait_label = result['label']
            self.efo_list[trait_id] = trait_label


    def check_efo(self):
        for trait_id in self.efo_list.keys():
            obo_id = trait_id.replace('_',':')
            ols_url = f'{self.ols_rest_url}{obo_id}'
            response = self.rest_api_call(ols_url)
            response = response.json()['_embedded']['terms']
            if len(response) == 1:
                response = response[0]

                if response['is_obsolete']:
                    self.efo_issue['obsolete'].append(trait_id)
            elif len(response) == 0:
                self.efo_issue['missing'].append(trait_id)




class PGS_Email():

    sender = 'auto@pgscatalog.org'
    title_prefix = 'Trait checks - '

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

    args = argparser.parse_args()

    pgs_rest_url = args.pgs_rest_url
    recipient = args.recipient

    efo_check = EFO_Check(pgs_rest_url)
    efo_check.fetch_efo_list()
    efo_check.check_efo()

    obsolete_count = len(efo_check.efo_issue['obsolete'])
    missing_count =  len(efo_check.efo_issue['missing'])
    title = ''
    content = ''
    if obsolete_count or missing_count:
        content += f'There were {efo_check.efo_count} traits checked.\n\n'
        if obsolete_count:
            title += f'{obsolete_count} obsolete traits'
            content += 'List of obsolete traits:\n'
            for trait_id in  efo_check.efo_issue['obsolete']:
                content += f"- {trait_id}: {efo_check.efo_list[trait_id]}\n"
        if missing_count:
            if title != '':
               title += ' and ' 
               content += '\n'
            title += f'{missing_count} missing traits'
            content += 'List of missing traits:\n'
            for trait_id in  efo_check.efo_issue['missing']:
                content += f"- {trait_id}: {efo_check.efo_list[trait_id]}\n"
        pgs_email = PGS_Email(title,content,recipient)
        pgs_email.send_message()
    else:
        title = 'all traits OK!'
        content = 'No obsolete nor missing traits'
    
    # Send results by email
    pgs_email = PGS_Email(title,content,recipient)
    pgs_email.send_message()

if __name__ == '__main__':
    main()