#!/usr/bin/env python3
"""
Retrieve the confluent cloud cluster limits in effect

Setup
=====
Create A confluent cloud API user and obtain the credentials first
"""

import argparse
import datetime
import requests
import logging
import pprint
from string import Template


L = logging.getLogger(__name__)

usage_limits_endpoint = "https://confluent.cloud/api/usage_limits?byok=false"
env_info_endpoint = "https://confluent.cloud/api/cmk/v2/clusters?environment="

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apikey', dest='apikey', help='Confluent Cloud APIKEY', required=True)
    parser.add_argument('--apisecret', dest='apisecret', help='Confluent Cloud APISECRET', required=True)
    parser.add_argument('--environment-id', dest='environment_id', help="Environment ID to get limits from, eg env-xg59z", required=True)
    parser.add_argument('--cluster-id', dest='cluster_id', help="Cluster ID to get limits from, eg lkc-w9ykm", required=True)
    parser.add_argument('--verbose', dest='verbose', default=False, action='store_true', help="Print debug info")

    args = parser.parse_args()

    if args.verbose:
      logging.basicConfig(level=logging.DEBUG)
      L.debug(args)


    # 1 - get platform usage limits
    response = requests.get(usage_limits_endpoint, auth=(args.apikey, args.apisecret))
    platform_usage_limits = response.json()
    L.debug("loaded platform limits OK")
    if args.verbose:
      pprint.pprint(platform_usage_limits)

    # 2 - get tier info for all clusters hosted in the environment
    response = requests.get(env_info_endpoint + args.environment_id, auth=(args.apikey, args.apisecret))
    environment_info = response.json()
    L.debug("loaded environment info OK")
    if args.verbose:
      pprint.pprint(environment_info)

    # 3 - Extract the cluster type - its at data[n][spec][config][kind]
    cluster_info = [cluster for cluster in environment_info["data"] if cluster["id"] == args.cluster_id]
    if cluster_info:
      L.debug(f"found cluster: {cluster_info}")
    else:
      raise RuntimeError(f"No such cluster: {args.cluster_id}")
    
    # 4 - Extract the cluster type - its at data[n][spec][config][kind]
    cluster_type = cluster_info[0]["spec"]["config"]["kind"]
    L.debug(f"found cluster type: {cluster_type}")

    # 5 - Extract the limits for this type of cluster
    cluster_usage_limits = platform_usage_limits["usage_limits"]["tier_limits"][cluster_type.upper()]
    if cluster_usage_limits:
      L.debug("found cluster usage limits!")
      if args.verbose:
        pprint.pprint(cluster_usage_limits)

      for limit_name, limit_data in cluster_usage_limits["cluster_limits"].items():
        limit_unit = limit_data['unit'] if limit_data['unit'] != "UNDEFINED" else ""
        print(f"{limit_name:<40} {limit_data['value']}{limit_unit}")

    else:
      raise RuntimeError("No cluster limits available for cluster type: {cluster_type}")

if __name__ == "__main__":
    main()