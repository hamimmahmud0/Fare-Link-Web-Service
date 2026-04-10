from flask import Flask, jsonify, request, abort, g
from util_defs import *
from endpoints_util import contact_utils
import sqlite3
from ctx import *
from endpoints_util import *
from exceptions import *

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


field_type_map = {
    int: 'INTEGER',
    bool: 'INTEGER',
    float: 'REAL',
    str: 'TEXT',
    bytes: 'BLOB',
    bytearray: 'BLOB',
    memoryview: 'BLOB',
    type(None): 'NULL',
}

json_field_type_map = {
    dict: 'OBJECT',
    list: 'ARRAY',
    tuple: 'ARRAY',
    str: 'STRING',
    int: 'INTEGER',
    float: 'NUMBER',
    bool: 'BOOLEAN',
    type(None): 'NULL',
}

def parse_field_name(name):
    return name.replace('-','_')

def parse_sql_key(fields):
    columns = ''
    for key in fields:
        key = parse_field_name(key)
        columns+= f'{key}, '
    columns=columns[:-2]
    return columns

def generate_field_query_string(fields, field_type_map = field_type_map):
    query_string = ''
    for key in fields:

        field_name = key
        field_type = fields[key]
        if not field_type in field_type_map:
            raise InvalidFieldTypeException("Field type not found")
        mapped_field_type = field_type_map[field_type]
        field_name_compitable = parse_field_name(field_name)
        pair = f'{field_name_compitable} {mapped_field_type}'
        query_string+=f'{pair}, '
    query_string=query_string[:-2]
    return query_string

def parse_json_to_query_string(data, ALL_FIELDS = contact_utils.ALL_FIELDS):
    query_str = ''
    print(data)
    for key in data:
        if not ALL_FIELDS[key] in json_field_type_map:
            print(f'Error: key: {key}')
            raise InvalidFieldTypeException
        
        if ALL_FIELDS[key] == str:
            query_str+= f'"{data[key]}", '
        else:    
            query_str+= f'{data[key]}, '
    query_str=query_str[:-2]
    print(f'parse_json_to_query_string: {query_str}')
    return query_str


def create_table(name, fields, exists=True):
    if_not_exists = ' IF NOT EXISTS'
    if not exists:
        if_not_exists = ''
    fields_string = generate_field_query_string(fields)
    db = get_db()

    print(f'Creating table: {name} for {fields}')
    db.execute(f'CREATE TABLE{if_not_exists} {name} (timestamp INTAGER PRIMARY KEY, {fields_string})')
    db.commit()

def insert_into_table(name, fields):
    db = get_db()
    columns = parse_sql_key(fields)
    cmd = f'INSERT INTO {name} (timestamp, {columns}) VALUES ({time.time_ns()}, {parse_json_to_query_string(fields)})'
    print(f'executing command: {cmd}')
    db.execute(cmd)
    db.commit()

def select_from_table(name, constraints,ALL_FIELDS=contact_utils.ALL_FIELDS):
    conds = ''
    for key in constraints:
        key_compitable = parse_field_name(key)
        if ALL_FIELDS[key] == str:
            conds += f'{key_compitable} = "{constraints[key]}" AND'
        else:
            conds += f'{key_compitable} = {constraints[key]} AND'
    conds=conds[:-4]
    db = get_db()
    cmd = f'SELECT * FROM {name} WHERE {conds}'
    print(f'DB: Executing {cmd}')
    rows = db.execute(cmd).fetchall()
    return {'data':[dict(row) for row in rows]}


    

# initialize

def init_db():
    db = get_db()
    # create a table announcement list
    create_table(CONTACT_TABLE_NAME,contact_utils.ALL_FIELDS)
    


# contact handlers
def add_contact(contact):
    db = get_db()
    insert_into_table(CONTACT_TABLE_NAME,contact)
    db.commit()
    
def search_contact(user_id):
    return select_from_table(CONTACT_TABLE_NAME,{
        'user-id':user_id
    })

def get_visible_contacts():
    return select_from_table(CONTACT_TABLE_NAME, {
        'visible':True
    })
    pass

# connected web service handlers
