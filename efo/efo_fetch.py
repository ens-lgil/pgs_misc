import argparse
import requests

items_separator = ' | '

def format_data(response):
    """ Format some of the data to match the format in the database. """
    data = {}

    # Label
    data['label'] = response['label']

    # URL
    data['url'] = response['iri']

    # Synonyms
    new_synonyms_string = ''
    new_synonyms = response['synonyms']
    if (new_synonyms):
        new_synonyms_string = items_separator.join(sorted(new_synonyms))
    data['synonyms'] = new_synonyms_string

    # Mapped terms
    new_mapped_terms_string = ''
    if 'database_cross_reference' in response['annotation']:
        new_mapped_terms = response['annotation']['database_cross_reference']
        if (new_mapped_terms):
            new_mapped_terms_string = items_separator.join(sorted(new_mapped_terms))
    data['mapped_terms'] = new_mapped_terms_string

    # Make description
    try:
        desc = response['obo_definition_citation'][0]
        str_desc = desc['definition']
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
            new_desc = items_separator.join(resp_desc)
        else:
            new_desc = resp_desc
            print(f'is a string')
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

        sql_values = []
        for key in sorted(efo_formatted_data.keys()):
            # print(f' - {key}: {efo_formatted_data[key]}')
            sql_values.append((key,efo_formatted_data[key]))
        
        # INSERT:
        cols = ','.join([x[0] for x in sql_values])
        vals = "'"+"','".join([x[1] for x in sql_values])+"'"
        sql_insert = f"INSERT INTO catalog_efotrait (id,{cols}) VALUES ('{trait_id}',{vals});"
        print(sql_insert)

        # UPDATE:
        # data = ','.join([f"{x[0]}='{x[1]}'" for x in sql_values])
        # sql_update = f"\nUPDATE catalog_efotrait SET {data} WHERE id='{trait_id}';"
        # print(sql_update)


    else:
        print("The script can't update the trait '"+trait_id+"': the API returned "+str(len(response))+" results.")


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--trait_ids", help='List of comma-separated EFO trait IDs (e.g. EFO_0009460,EFO_0004682)', required=True, metavar='TRAITS_LIST')

    args = argparser.parse_args()

    traits = args.trait_ids

    for trait in traits.split(','):
        get_trait(trait)


if __name__ == '__main__':
    main()