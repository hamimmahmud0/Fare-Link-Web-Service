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


def build_condition_string(constraints, ALL_FIELDS=contact_utils.ALL_FIELDS):
    conds = ''
    for key in constraints:
        key_compitable = parse_field_name(key)
        if ALL_FIELDS[key] == str:
            conds += f'{key_compitable} = "{constraints[key]}" AND '
        else:
            conds += f'{key_compitable} = {constraints[key]} AND '
    return conds[:-5]


def build_update_string(fields, ALL_FIELDS=contact_utils.ALL_FIELDS):
    update_str = ''
    for key in fields:
        key_compitable = parse_field_name(key)
        if ALL_FIELDS[key] == str:
            update_str += f'{key_compitable} = "{fields[key]}", '
        else:
            update_str += f'{key_compitable} = {fields[key]}, '
    return update_str[:-2]

def get_conflict_str(fields, conflict):
    conflict_str = ''

    for key in fields:
        if key == conflict:
            continue
        sql_key = parse_field_name(key)
        conflict_str += f'{sql_key} = excluded.{sql_key}, '
    
    return conflict_str[:-2]



def create_table(name, fields, exists=True):
    if_not_exists = ' IF NOT EXISTS'
    if not exists:
        if_not_exists = ''
    fields_string = generate_field_query_string(fields)
    db = get_db()

    print(f'Creating table: {name} for {fields}')
    db.execute(f'CREATE TABLE{if_not_exists} {name} (timestamp INTAGER PRIMARY KEY, {fields_string})')
    db.commit()


def create_unique_index(table_name, field_name):
    db = get_db()
    sql_field_name = parse_field_name(field_name)
    index_name = f'{table_name}_{sql_field_name}_unique_idx'
    db.execute(
        f'CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name} ({sql_field_name})'
    )
    db.commit()

def insert_into_table(name, fields,conflict=None):
    db = get_db()
    columns = parse_sql_key(fields)
    conflict_str = ''
    if conflict:
        conflict_str = f' ON CONFLICT({parse_field_name(conflict)}) DO UPDATE SET {get_conflict_str(fields, conflict)}'
    cmd = f'INSERT INTO {name} (timestamp, {columns}) VALUES ({time.time_ns()}, {parse_json_to_query_string(fields)}){conflict_str}'
    print(f'DB:insert_into_table: executing command: {cmd}')
    db.execute(cmd)
    db.commit()

def select_from_table(
    name,
    constraints,
    ALL_FIELDS=contact_utils.ALL_FIELDS,
    limit=None,
    offset=None,
    order_by=None,
    order='ASC'
):
    conds = build_condition_string(constraints, ALL_FIELDS=ALL_FIELDS)
    db = get_db()
    cmd = f'SELECT * FROM {name} WHERE {conds}'

    if order_by is not None:
        cmd += f' ORDER BY {parse_field_name(order_by)} {order}'

    if limit is not None:
        cmd += f' LIMIT {limit}'

    if offset is not None:
        cmd += f' OFFSET {offset}'

    print(f'DB:select_from_table: executing command{cmd}')
    rows = db.execute(cmd).fetchall()
    return {'data':[dict(row) for row in rows]}

def update_in_table(name,fields,constraints, ALL_FIELDS=contact_utils.ALL_FIELDS):
    db = get_db()
    update_str = build_update_string(fields, ALL_FIELDS=ALL_FIELDS)
    conds = build_condition_string(constraints, ALL_FIELDS=ALL_FIELDS)
    cmd = f'UPDATE {name} SET {update_str} WHERE {conds}'
    print(f'DB:update_in_table: executing command: {cmd}')
    cursor = db.execute(cmd)
    db.commit()
    return cursor.rowcount
    
def delete_in_table(name,constraints=None, ALL_FIELDS=contact_utils.ALL_FIELDS, condition_str=None):
    db = get_db()
    conds = condition_str
    if conds is None:
        conds = build_condition_string(constraints, ALL_FIELDS=ALL_FIELDS)
    cmd = f'DELETE FROM {name} WHERE {conds}'
    print(f'DB:delete_in_table: executing command: {cmd}')
    cursor = db.execute(cmd)
    db.commit()
    return cursor.rowcount

# initialize

def init_db():
    db = get_db()
    # create a table announcement list
    create_table(CONTACT_TABLE_NAME,contact_utils.ALL_FIELDS)
    create_unique_index(CONTACT_TABLE_NAME, 'user-id')
    


# contact handlers
def add_contact(contact):
    db = get_db()
    insert_into_table(CONTACT_TABLE_NAME,contact,conflict='user-id')
    db.commit()
    
def search_contact(user_id):
    return select_from_table(CONTACT_TABLE_NAME,{
        'user-id':user_id
    })

def get_visible_contacts(page = 1, limit = 50):
    offset = (page - 1) * limit
    return select_from_table(
        CONTACT_TABLE_NAME,
        {
            'visible':True
        },
        limit=limit,
        offset=offset,
        order_by='timestamp',
        order='DESC'
    )

def remove_expired_contacts():
    # remove all contacts where entry.timestamp + entry.expire * 60 * 10^6 < current_timestamp_in_ns
    current_timestamp = time.time_ns()
    condition_str = f'timestamp + (expire * 1000000000) < {current_timestamp}'
    return delete_in_table(CONTACT_TABLE_NAME, condition_str=condition_str)
# connected web service handlers
