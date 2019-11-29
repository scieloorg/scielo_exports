'''
Este script retorna objeto tipo dict de uma consulta ao Kibana.
A Query do Kibana deverá ser passada como argumento.
Exemplo:
query = "_type: article AND collection: scl AND processing_date: (2019-07* OR 2019-08*)"
'''
import csv
import io
import json
import pycurl
import sys
import platform


def export2csv(filename, query):
    # Exporta a lista de PIDs para arquivo .csv
    data = pids_tuples(query)

    with open(filename, 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['collection', 'pid'])
        for row in data:
            csv_out.writerow(row)

    return ("Checkout the %s" % filename)


def total_pids(query):
    # Retorna o total de pids recuperado

    return len(pids_tuples(query))


def pids_tuples(query):
    # Retorna uma lista de tuplas (collection, pid)

    rjson = search_kibana(query)

    pids_tuples = []

    for pid in rjson['responses'][0]['aggregations']['2']['buckets']:
        pids_tuples.append(tuple(pid['key'].split('_')))

    return pids_tuples


def search_kibana(query):
    # Retorna o resultado da API do Kibana
    data = (
        '{"index":"publication","search_type":"count","ignore_unavailable":true}\
        \n{"size":0,"query":{"query_string":{"analyze_wildcard":true,"query":"%s"}},\
        "aggs":{"2":{"terms":{"field":"id","size":0,"order":{"_count":"desc"}}}}}\n' % query)

    r = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'http://kibana.scielo.org/elasticsearch/_msearch?pretty')
    c.setopt(c.WRITEFUNCTION, r.write)
    c.setopt(c.HTTPHEADER, [
             'Content-Type: application/json', 'Accept-Charset: UTF-8'])
    c.setopt(c.POSTFIELDS, data)
    c.perform()
    c.close()
    if platform.system() == 'Windows':
        rjson = json.loads(r.getvalue().decode())
    else:
        rjson = json.loads(r.getvalue())

    return rjson
