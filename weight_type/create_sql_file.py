
sql_file = open('weight_types_cmd.sql', 'w')

with open('weight_types_all.txt') as f:
    for line in f:
        (pgs_id,wt) = line.rstrip('\n').split('\t')
        if wt != 'NR':
            sql_cmd = f'UPDATE catalog_score SET weight_type=\'{wt}\' WHERE id=\'{pgs_id}\';\n'
            sql_file.write(sql_cmd)
sql_file.close()