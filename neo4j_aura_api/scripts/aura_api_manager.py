#! /usr/bin/env python3

import os
import dotenv
import json
import subprocess
import datetime
import argparse
from urllib.parse import urljoin
import neo4j
import graphdatascience

# TEMP CONSTANTS
api_base = 'https://api.neo4j.io/'
tmp_dir = './.tmp'
# I'll need to replace this later with either something interactive or a standard JSON template that will contain this information. 
default_cred_file = os.path.join(tmp_dir, "neo4j-api-creds.txt") 

cred_file = default_cred_file

# Input API credentials file and output dictionary with CLIENT_ID CLIENT_SECRET and CLIENT_NAME
def get_creds(credentials_file=None):
    if credentials_file:
        api_creds = dotenv.dotenv_values(credentials_file)
    return dict(api_creds)

def refresh_token(api_creds, api_base, tmp_dir):
    api_endpoint = urljoin(api_base, '/oauth/token')

    #Check if tmp_dir exists
    token_file = os.path.join(tmp_dir, 'bearer_token')
    if os.path.isdir(tmp_dir):
        if os.path.isfile(token_file):
            token_file_exists = True
    else:
        confirm_create = input('Create tmp directory {}? '.format(tmp_dir))
        if confirm_create.casefold() == 'y':
            mkdir_cmd = 'mkdir ' + tmp_dir
            os.system(mkdir_cmd) 
            
    curl_cmd = "curl --request POST '{}' --user '{}:{}' --header 'Content-Type: application/x-www-form-urlencoded' --data-urlencode 'grant_type=client_credentials'".format(api_endpoint, api_creds['CLIENT_ID'], api_creds['CLIENT_SECRET'], api_creds['CLIENT_NAME'])
    result = json.loads(subprocess.check_output(curl_cmd, shell=True))
    access_token = result['access_token']
    expires_in = result['expires_in']

    now = datetime.datetime.now()
    expiration = (now + datetime.timedelta(0, expires_in)).isoformat()

    bearer_token = {
        'access_token': access_token,
        'expiration': expiration
    }

    with open(token_file, "w") as outfile:
        json.dump(bearer_token, outfile, indent=4)

    access_token = bearer_token['access_token']
    return access_token 

# Check if token is valid for at least 5 more minutes (later on can add a variable to adjust the time window)
def validate_token(bearer_token):
    token_valid = False
    token_expiration = datetime.datetime.fromisoformat(str(bearer_token['expiration']))
    delta_time = (token_expiration - datetime.datetime.now()).total_seconds()

    print('delta_time:', delta_time)

    # Make sure token has at least 5 more minutes of validity left
    if delta_time > 300:
        print('token_expiration:', token_expiration)
        print('Token is valid for {} more minutes'.format(delta_time/60)) 
        token_valid = True

    return token_valid

# Input API credentials ans return an access token for the API
def authenticate_api(api_creds, api_base, tmp_dir):

    api_endpoint = urljoin(api_base, '/oauth/token')
    token_file_exists = False 
    valid_token = False

    #Check if tmp_dir exists
    token_file = os.path.join(tmp_dir, 'bearer_token')
    if os.path.isdir(tmp_dir):
        if os.path.isfile(token_file):
            token_file_exists = True
    else:
        confirm_create = input('Create tmp directory {}? '.format(tmp_dir))
        if confirm_create.casefold() == 'y':
            mkdir_cmd = 'mkdir ' + tmp_dir
            os.system(mkdir_cmd)


    if token_file_exists:
        with open(token_file, "r") as infile:
            bearer_token = json.load(infile)

        valid_token = validate_token(bearer_token)

    # If there is no valid token, then generate a new one
    if valid_token:
        access_token = bearer_token['access_token']
    else:
        access_token = refresh_token(api_creds, api_base, tmp_dir)

    return access_token


def list_tenants(access_token, api_base, tenant_id=None):
    #api_endpoint = 'https://api.neo4j.io/v1/tenants'

    api_endpoint = urljoin(api_base, '/v1/tenants')

    aura_tenants = {}

    if tenant_id:
        api_endpoint += '/' + tenant_id

    print()
    print('api_endpoint:', api_endpoint)
    print()

    list_cmd = "curl -s -X 'GET' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}'".format(api_endpoint, access_token)
    
    list_tenants = dict(json.loads(subprocess.check_output(list_cmd, shell=True)))['data']
    for item in list_tenants:
        aura_tenants[item['id']] = {}
        aura_tenants[item['id']]['id'] = item['id'] 
        aura_tenants[item['id']]['name'] = item['name'] 

    return aura_tenants


def tenant_info(access_token, api_base, tenant_id):
    api_endpoint = urljoin(api_base, '/v1/tenants/' + tenant_id)

    tenant_data = {}

    print()
    print('api_endpoint:', api_endpoint)
    print()

    info_cmd = "curl -s -X 'GET' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}'".format(api_endpoint, access_token)
#    print('info_cmd:')
#    print(info_cmd)

    tenant_info = json.loads(subprocess.check_output(info_cmd, shell=True))['data']
#    print('tenant_info:', tenant_info)

    print()
    for item in tenant_info:
        #print(item, '=', tenant_info[item])
        tenant_data[tenant_info['id']] = {}
        tenant_data[tenant_info['id']]['tenant_id'] = tenant_info['id']
        tenant_data[tenant_info['id']]['tenant_name'] = tenant_info['name'] 
        tenant_data[tenant_info['id']]['instance_configurations'] = list(tenant_info['instance_configurations'])

    return tenant_data


def list_instances(access_token, api_base, tenant_id=None):
    api_endpoint = urljoin(api_base, '/v1/instances') 

    aura_instances = {}

    print()
    print('api_endpoint:', api_endpoint)
    print()

    list_cmd = "curl -s -X 'GET' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}'".format(api_endpoint, access_token)
#    print('list_cmd:')
#    print(list_cmd)

    list_instances = json.loads(subprocess.check_output(list_cmd, shell=True))['data']
    print('aura_instances:')
    for instance in list_instances:
        print(instance)
        aura_instances[instance['id']] = {}
        aura_instances[instance['id']]['instance_id'] = instance['id'] 
        aura_instances[instance['id']]['instance_name'] = instance['name'] 
        aura_instances[instance['id']]['cloud_provider'] = instance['cloud_provider'] 
        aura_instances[instance['id']]['tenant_id'] = instance['tenant_id'] 

    return aura_instances


def instance_info(access_token, api_base, instance_id):
    api_endpoint = urljoin(api_base, '/v1/instances/' + instance_id)

    instance_data = {}

    print()
    print('api_endpoint:', api_endpoint)
    print()

    info_cmd = "curl -s -X 'GET' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}'".format(api_endpoint, access_token)

    api_response = json.loads(subprocess.check_output(info_cmd, shell=True))
    print('api_response:', api_response)

    if 'data' in api_response:
        response_data = api_response['data']
        print('response_data:')
        print(response_data)
        instance_status = response_data['status']
        print('instance_status:', instance_status)

    return response_data

def deploy_instance(access_token, api_base, instance_name):
    api_endpoint = urljoin(api_base, '/v1/instances')

    instance_details = {}

    print()
    print('api_endpoint:', api_endpoint)
    print()
    request_body = {
        "version": "5",
        "region": "europe-west1",
        "memory": "16GB",
        "name": instance_name,
        "type": "professional-ds",
        "tenant_id": "e35ffd72-566a-5163-bf80-41a65f4bd5e0",
        "cloud_provider": "gcp"
    }

    print('request body type (before):', type(request_body))
    json_request_body = json.dumps(request_body)
    print('request body type (after):', type(json_request_body))

    curl_cmd = "curl -s -X 'POST' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}' -H 'Content-Type: application/json'".format(api_endpoint, access_token)
    curl_cmd += " -d '{}'".format(json_request_body)
    print('curl_cmd:')
    print(curl_cmd)
    api_response = json.loads(subprocess.check_output(curl_cmd, shell=True))

    print('New instance created:')
    print(api_response)
    
    response_data = api_response['data']
    
    instance_details['id'] = response_data['id']
    instance_details['name'] = response_data['name']
    instance_details['connection_url'] = response_data['connection_url']
    instance_details['password'] = response_data['password']
    instance_details['username'] = response_data['username']
    instance_details['cloud_provider'] = response_data['cloud_provider']
    instance_details['region'] = response_data['region']
    instance_details['tenant_id'] = response_data['tenant_id']
    instance_details['type'] = response_data['type']

    print()
    print('instance_details:')
    for item in instance_details:
        print(item, '=', instance_details[item])
    print()

    return instance_details

def update_instance(access_token, api_base, instance_id, instance_name, instance_size):
    api_endpoint = urljoin(api_base, '/v1/instances/' + instance_id)

    print()
    print('api_endpoint:', api_endpoint)
    print()

    request_body = {}
    if instance_name:
        request_body['name'] = instance_name
    if instance_size:
        request_body['memory'] = str(instance_size) + "GB"

    json_request_body = json.dumps(request_body)
    print('json_request_body:', json_request_body)

    curl_cmd = "curl -s -X 'PATCH' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}' -H 'Content-Type: application/json'".format(api_endpoint, access_token)
    curl_cmd += " -d '{}'".format(json_request_body)
    print('curl_cmd:')
    print(curl_cmd)

    api_response = json.loads(subprocess.check_output(curl_cmd, shell=True))

    print('Instance updated:')
    print(api_response)


def delete_instance(access_token, api_base, instance_id):
    api_endpoint = urljoin(api_base, '/v1/instances/' + instance_id)

    print()
    print('api_endpoint:', api_endpoint)
    print()

    curl_cmd = "curl -s -X 'DELETE' '{}' -H 'accept: application/json' -H 'Authorization: Bearer {}'".format(api_endpoint, access_token)

    print("curl_cmd:")
    print(curl_cmd)

    api_response = json.loads(subprocess.check_output(curl_cmd, shell=True))

    print('api_response:')
    print(api_response)

    if 'data' in api_response:
        instance_id = api_response['data']['id']
        instance_name = api_response['data']['name']
        print('instance_id:', instance_id)
        print('instance_name:', instance_name)

        cred_filename = os.path.join(tmp_dir, 'Neo4j-' + instance_id + '-' + instance_name + '.txt')
        print('cred_filename:', cred_filename)
        
        # Delete the credential file if it still exists
        print('Deleting instance credential file {}'.format(cred_filename))
        if os.path.isfile(cred_filename):
            os.system('rm ' + cred_filename)
    


def export_credentials(instance_details):
    filename = 'Neo4j-' + instance_details['id'] + '-' + instance_details['name'] + '.txt' 
    credentials_file = ""
    credentials_file += 'NEO4J_URI=' + instance_details['connection_url'] + '\n'
    credentials_file += 'NEO4J_USERNAME=' + instance_details['username'] + '\n'
    credentials_file += 'NEO4J_PASSWORD=' + instance_details['password'] + '\n'
    credentials_file += 'NEO4J_INSTANCEID=' + instance_details['id'] + '\n'
    credentials_file += 'NEO4J_INSTANCENAME=' + instance_details['name'] + '\n'

    cred_file = os.path.join(tmp_dir, filename)

    with open(cred_file, 'w') as f:
        f.write(credentials_file)


def display_dict(dictionary, description=None):
    if description:
        print(description)
    
    for l1 in dictionary:
        print(l1, 'is of type', type(dictionary[l1]))
        if isinstance(dictionary[l1], str):
            print(l1 + ': ' + dictionary[l1])
        elif isinstance(dictionary[l1], dict):
            for l2 in dictionary[l1]:
                print('\t' + l2, 'is of type', type(dictionary[l1][l2]))
                if isinstance(dictionary[l1][l2], str):
                    print('\t' + l2 + ': ' + dictionary[l1][l2])
                elif isinstance(dictionary[l1][l2], list):
                    print('\t' + l2 + ':' )
                    for l3 in dictionary[l1][l2]:
                        print('\t\t' + str(l3))

def parseargs(defaults=None, config_files=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-credentials', metavar="CREDENTIALS_FILE", help="Aura API credentials file")
    parser.add_argument('--list-instances', action='store_true', help="List Aura instances")
    parser.add_argument('--list-tenants', action='store_true', help="List Aura tenants")
    parser.add_argument('--tenant-info', metavar="TENANT_ID")
    parser.add_argument('--instance-info', metavar="INSTANCE_ID")
    parser.add_argument('--deploy-instance', metavar="INSTANCE_NAME", help="Deploy new Aura instance")
    parser.add_argument('--update-instance', metavar="INSTANCE_NAME", help="Rename or resize Aura instance")
    parser.add_argument('--delete-instance', metavar="INSTANCE_ID", help="Delete Aura instance")
    parser.add_argument('--instance-name', metavar="INSTANCE_NAME", help="Instance name")
    parser.add_argument('--instance-size', metavar="INSTANCE_SIZE", help="Instance size in GB")
    parser.add_argument('---id', metavar="INSTANCE_ID", help="Aura instance ID")
    parser.add_argument('--tenant-id', metavar="TENANT_ID", help="Tenant ID")
    parser.add_argument('--refresh-token', action='store_true', help="Refresh bearer token")
    args = parser.parse_args()	
    return vars(args)

def main():
    args = parseargs()

    if args['api_credentials']:
        api_creds = get_creds(args['api_credentials'])

    api_creds = get_creds(cred_file)
    access_token = authenticate_api(api_creds, api_base, tmp_dir)

    if args['refresh_token']:
        access_token = refresh_token(api_creds, api_base, tmp_dir)
        print('New access token:')
        print(access_token)

    if args['list_tenants']:
        print()
        print('list_tenants:')
        aura_tenants = list_tenants(access_token, api_base, args['tenant_id'])
        print()
        print('Aura Tenants:')
        print('-------------')
        for tenant in aura_tenants:
            print(aura_tenants[tenant])
        print()

    if args['tenant_info']:
        print()
        print('tenant_info:')
        tenant_data = tenant_info(access_token, api_base, args['tenant_info'])
        display_dict(tenant_data, description="Tenant Infomania")
        #print('tenant_data:')
        #print(tenant_data)

    if args['instance_info']:
        print()
        print('instance_info:')
        instance_data = instance_info(access_token, api_base, args['instance_info'])
        print('instance_data:')
        print(instance_data)

    if args['list_instances']:
        print('list_instances:')
        aura_instances = list_instances(access_token, api_base, args['tenant_id'])
        print()
        print('Aura Instances:')
        print('---------------')
        for instance in aura_instances:
            print(aura_instances[instance]['instance_name'])
            for attr in aura_instances[instance]:
                print( attr + ': ' + aura_instances[instance][attr])
            print()
        
    if args['deploy_instance']:
        instance_details = deploy_instance(access_token, api_base, args['deploy_instance'])
        export_credentials(instance_details)

    if args['update_instance']:
        instance_details = update_instance(access_token, api_base, args['update_instance'], args['instance_name'], args['instance_size'])
        
    if args['delete_instance']:
        delete_instance(access_token, api_base, args['delete_instance'])



if __name__ == '__main__':
    main()
