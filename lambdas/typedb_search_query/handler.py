#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 10:15:34 2022

@author: imane.hafnaoui
"""
import json
import logging
import os
from typedb.client import TransactionType, SessionType, TypeDB
from datetime import datetime


return_vals = ['title', 'summary', 'document_uid', 'legislative_origins','regulator_id', 'uri', 'date_uploaded', 'data_published', 'version']
leg_vals = ['url', 'title', 'leg_type', 'leg_division']

LOGGER = logging.getLogger()
LOGGER.setLevel(int(os.environ.get("LOGGING_LEVEL", logging.INFO)))


############################################
# HELPER FUNCTIONS
############################################
def format_datetime(date): return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")
def get_select_dict(results:dict, selc:list):    return {k:(format_datetime(v) if type(v)==datetime else v)for k,v in results.items() if k in selc}
def getUniqueResult(results):
    results = [(i.get_type().get_label().name(), i.get_value()) for a in results for i in a.concepts() if i.is_attribute()]
    return results

def matchgroupquery(query, session):
    with session.transaction(TransactionType.READ) as transaction:
        print("Query:\n %s"%query)
        iterator = transaction.query().match_group(query)
        results = [ans for ans in iterator]
        return results 

def validate_env_variable(env_var_name):
    LOGGER.debug(f"Getting the value of the environment variable: {env_var_name}")

    try:
        env_variable = os.environ[env_var_name]
    except KeyError:
        raise Exception(f"Please, set environment variable {env_var_name}")

    if not env_variable:
        raise Exception(f"Please, provide environment variable {env_var_name}")

    return env_variable

############################################
# LAMBDA HANDLER
############################################


def lambda_handler(event, context):

    LOGGER.debug("Received event: " + json.dumps(event, indent=2))

    TYPEDB_IP = validate_env_variable('TYPEDB_SERVER_IP')
    TYPEDB_PORT = validate_env_variable('TYPEDB_SERVER_PORT')
    TYPEDB_DATABASE_NAME = validate_env_variable('TYPEDB_DATABASE_NAME')

    client = TypeDB.core_client(TYPEDB_IP + ':'+TYPEDB_PORT)
    session = client.session(TYPEDB_DATABASE_NAME, SessionType.DATA)
    
    if len(event)==0:
        LOGGER.error("Did not receive any search parameters. This really shouldn't be showing...Sorcery?!")
    else:
        # Build TQL query from search params
        query = 'match $x isa regulatoryDocument, has attribute $attribute'
        if event.get('id'):
            query += f', has document_uid "{event["id"]}"' 
        else:
            if event.get('keyword'):
                query += ''.join([f', has keyword "{kw}"' for kw in event['keyword'].split(' ')])
            if event.get('title'):
                query += f', has title $title; $title contains "{event["title"]}"'
        
        query += '; get $attribute, $x; group $x;'
        
        
        # Query the graph database for reg. documents
        LOGGER.info("Querying the graph for reg. documents")
        ans = matchgroupquery(query, session)[:10]
        res = [dict(getUniqueResult(a.concept_maps())) for a in ans]
        LOGGER.info(f"Ret -> {len(res)}")
        # Query the graph database for legislative origins
        LOGGER.info("Querying the graph for legislative origins")
        for doc in res:
            query = f'match $x isa regulatoryDocument, has node_id "{doc["node_id"]}";' + \
            '$y isa legislation, has attribute $attribute;' + \
            ' (issued:$x,issuedFor:$y) isa publication;' + \
                ' get $attribute, $y; group $y;'
            doc['legislative_origins'] = [get_select_dict(dict(getUniqueResult(a.concept_maps())), leg_vals) for a in matchgroupquery(query, session)]
        docs = [get_select_dict(doc, return_vals) for doc in res]
        out = {
            "total_search_results": len(docs),
            "documents": docs
            }
        return out
