# coding: utf-8
'''
Este script retorna objeto tipo dict de uma consulta ao Kibana.
A Query do Kibana deverá ser passada como argumento.
Exemplo:
query = "_type: article AND collection: scl AND processing_date: (2019-07* OR 2019-08*)"
'''
import csv

from elasticsearch import Elasticsearch


def export2csv(filename, query):
    # Exporta a lista de PIDs para arquivo .csv
    data = pids_tuples(query)

    with open(filename, 'w') as out:
        csv_out = csv.writer(out)
        header = ['collection', 'pid']
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

    pids_tuples = [(i['_id'][:3],i['_id'][4:]) for i in rjson['hits']['hits']]
    pids_tuples.sort()

    return pids_tuples


def search_kibana(query):
    es = Elasticsearch([{'host':'kibana.scielo.org', 'port':5601, 'url_prefix': 'elasticsearch'}])

    total = es.search(index="publication", q=query)['hits']['total']

    rjson = es.search(index="publication", q=query, size=total)

    return rjson
