# Automatically update Google Cloud DNS during Compute Engine (GCE) instance startup or shutdown

[![Build Status](https://travis-ci.org/crosslibs/autoupdate-cloud-dns-upon-gce-start-stop.svg?branch=master)](https://travis-ci.org/crosslibs/autoupdate-cloud-dns-upon-gce-start-stop)

## Pre-requisites
The DNS record (A) addition or deletion to/from Cloud DNS managed zone is done using a python script. The following are necessary for successful execution of the script:

* python3 and pip3 installed
* The service account attached to the GCE instance must have access to `https://www.googleapis.com/auth/cloud-platform` scope
* Cloud DNS with a managed zone (public / private). If you do not have a managed zone in Cloud DNS, you can set it up by following the documentation [here](https://cloud.google.com/dns/zones/). Here is an example:
```
e.g. Create a public managed zone for example.com:

> gcloud dns managed-zones create example-com \
    --dns-name="example.com" \
    --visibility=public

e.g. Create a private managed zone for example.com:

> gcloud dns managed-zones create example-com \
    --dns-name="example.com" \
    --visibility=private
```
* Further, each GCE instance must also have Cloud DNS project id, managed zone as well as domain name set through metadata using keys  `dns-project`, `dns-zone` and `dns-domain` respectively. Further, you also need to set the TTL for the DNS record by passing value (in seconds) for `dns-ttl` key.  (e.g. `--metadata dns-project=abcd,dns-zone=example-com,dns-domain=example.com,dns-ttl=3600`). Please refer [here](https://cloud.google.com/compute/docs/metadata#custom) for more information on setting custom metadata.

## Add A record during GCE instance startup and Remove A record during GCE instance shutdown

Pass the domain, startup and shutdown scripts as part of GCE instance metadata (`gcloud compute instances create` command)

```
--metadata dns-project=project-id,dns-zone=example-com,dns-domain=example.com,dns-ttl=3600,startup-script-url=gs://cloud-dns-scripts/startup.sh,shutdown-script-url=gs://cloud-dns-scripts/shutdown.sh
```

## End to End example

Set environment variables
```
export DNS_PROJECT_ID=<your-dns-project-id>
export DNS_ZONE_NAME=example-com
export DNS_DOMAIN=example.com
export DNS_TTL=3600
export INSTANCE_NAME=instance-1

```
Create a Cloud DNS Managed Zone (private) for `example.com` domain with zone name as `example-com`
```
> gcloud dns managed-zones create $DNS_ZONE_NAME \
    --dns-name=$DNS_DOMAIN \
    --visibility=private
```
Create a GCE instance with instance name `instance-1`
```
> gcloud compute instances create $INSTANCE_NAME \
    --image=debian-9-stretch-v20191121 \
    --image-project=debian-cloud \
    --scopes=cloud-platform	\
    --metadata dns-project=$DNS_PROJECT_ID,dns-zone=$DNS_ZONE_NAME,dns-domain=$DNS_DOMAIN,dns-ttl=$DNS_TTL,startup-script-url=gs://cloud-dns-scripts/startup.sh,shutdown-script-url=gs://cloud-dns-scripts/shutdown.sh
```
Run the following command and check that it returns exactly one item. Also verify that the DNS record is set correctly.
```
> gcloud dns record-sets list --zone=$DNS_ZONE_NAME --name="$INSTANCE_NAME.$DNS_DOMAIN" --type=A
```
Delete the `instance-1` GCE instance
```
> gcloud compute instances delete instance-1
```
Run the following command and check that it returns `0` items.
```
> gcloud dns record-sets list --zone=$DNS_ZONE_NAME --name="$INSTANCE_NAME.$DNS_DOMAIN" --type=A
```
Delete the managed DNS zone
```
> gcloud dns managed-zones delete $DNS_ZONE_NAME
```