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
from string import Template


L = logging.getLogger(__name__)

metrics_request_template="""{
  "aggregations": [
    {
      "metric": "io.confluent.kafka.server/$metric_name"
    }
  ],
  "filter": {
    "field": "resource.kafka.id",
    "op": "EQ",
    "value": "$cluster_id"
  },
  "granularity": "PT1M",
  "intervals": [
    "$interval"
  ],
  "limit": 1
}"""

metrics_endpoint = "https://api.telemetry.confluent.cloud/v2/metrics/cloud/query"

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apikey', dest='apikey', help='Confluent Cloud APIKEY', required=True)
    parser.add_argument('--apisecret', dest='apisecret', help='Confluent Cloud APISECRET', required=True)
    parser.add_argument('--cluster-id', dest='cluster_id', help="Cluster ID to get limits from, eg lkc-w9ykm", required=True)
    parser.add_argument('--verbose', dest='verbose', default=False, action='store_true', help="Print debug info")

    args = parser.parse_args()

    if args.verbose:
      logging.basicConfig(level=logging.DEBUG)
      L.debug(args)
    

    # Example of how to discover system-wide available metrics
    #curl 'https://api.telemetry.confluent.cloud/v2/metrics/cloud/descriptors/metrics?resource_type=kafka' --user "$TOKEN"

    # CC UI <--> Metrics API mapping
    # ==============================
    #   Ingress = received_bytes
    #	  Egress = sent_bytes
    # 	Total client connections = active_connection_count
    #	  Requests = request_count
    want_metrics = ["received_bytes"] #, "sent_bytes", "active_connection_count", "request_count"]

    # https://stackoverflow.com/a/28147286/3441106
    time_now_string = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    time_one_hour_ago_string = (datetime.datetime.now() - datetime.timedelta(hours = 1)).astimezone().replace(microsecond=0).isoformat()
    interval = f"{time_one_hour_ago_string}/{time_now_string}"
    for metric_name in want_metrics:
      L.debug(f"getting metric: {metric_name}")

      payload = Template(metrics_request_template).substitute({
        "metric_name": metric_name, 
        "cluster_id": args.cluster_id,
        "interval": interval
      })
      L.debug(payload)


      response = requests.post(metrics_endpoint, data=payload, auth=(args.apikey, args.apisecret), headers={'Content-type': 'application/json'})
      L.debug(response)
      L.debug(response.json())


if __name__ == "__main__":
    main()