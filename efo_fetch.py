import argparse
import requests

items_separator = ' | '

def format_data(response):
    """ Format some of the data to match the format in the database. """
    data = {}
    # Make description
    try:
        desc = response['obo_definition_citation'][0]
        str_desc = desc['definition']
        print(f'obo_definition_citation: {str_desc}')
        for x in desc['oboXrefs']:
            if x['database'] != None:
                if x['id'] != None:
                    str_desc += ' [{}: {}]'.format(x['database'], x['id'])
                else:
                    str_desc += ' [{}]'.format(x['database'])
        new_desc = str_desc
    except:
        resp_desc = response["description"]
        if type(resp_desc) == list:
            print(f'is a list')
            new_desc = items_separator.join(resp_desc)
        else:
            new_desc = resp_desc
            print(f'is a string')
        print(f'description: {new_desc}')
    data['description'] = new_desc

    return data


def get_trait(trait_id):
    response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%trait_id.replace('_', ':'))
    response = response.json()['_embedded']['terms']
    if len(response) == 1:
        response = response[0]
        new_label = response['label']

        if response['is_obsolete']:
            obsolete_msg = f'The trait "{new_label}" ({trait_id}) is labelled as obsolete by EFO!'
            print(f'WARNING: {obsolete_msg}')


        # Synonyms, Mapped terms and description
        efo_formatted_data = format_data(response)

        efo_formatted_data['description']

    else:
        print("The script can't update the trait '"+trait_id+"': the API returned "+str(len(response))+" results.")


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--trait_ids", help='List of comma-separated EFO trait IDs (e.g. EFO_0009460,EFO_0004682)', required=True, metavar='INPUT_DIR')

    args = argparser.parse_args()

    traits = args.trait_ids

    for trait in traits.split(','):
        print(f'\n> {trait}')
        get_trait(trait)


if __name__ == '__main__':
    main()