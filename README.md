# Daraja Integration using Django 3.2

- This is an mpesa integration generic APIs

## Plan Part 1

- [x] Authentication Credentials
- [x] STK push Integration (Async)
- [ ] C2B integration
- [ ] B2C integration (Bulk payments)

## Part 2

- [ ] Slack Integration

## Part 3

- [x] ElasticSearch
  - use `chmod +x elasticsearch.sh` and `./elasticsearch.sh` to spin a local elasticsearch docker image
- [x] Kibana Dashboard
  - [Kibana Configs](https://stackoverflow.com/questions/69791608/unable-to-retrieve-version-information-from-elasticsearch-nodes-request-timed-o)
- [ ] Analytics

## Part 4

- [ ] Card Integration

## Git Precommit Hook

To use the git precommit hook run the following commands

`chmod +x precommit.sh`
`./precommit.sh`

## Configs in .env

`touch .env`

paste and edit the missing configs

SECRET_KEY=secret key
DATABASE_USERNAME=
DATABASE_USER=
DATABASE_PORT=
DATABASE_PASSWORD=
DEBUG=True
API_HOST_NAME=backend host name
CODE_ENV=local

## daraja sanbox configs

DARAJA_SANDBOX_CONSUMER_KEY=key
DARAJA_SANDBOX_CONSUMER_SECRET=secret
DARAJA_SANDBOX_PASS_KEY=pass_key
DARAJA_SANDBOX_BUSINESS_SHORT_CODE=174379
DARAJA_SANDBOX_ACCESS_URL=<https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials>
DARAJA_SANDBOX_STKPUSH_URL=<https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest>
DARAJA_SANDBOX_STKPUSH_QUERY_URL=<https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query>
DARAJA_SANDBOX_C2B_REGISTER_URL=<https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl>

## daraja live configs

DARAJA_LIVE_CONSUMER_KEY=
DARAJA_LIVE_CONSUMER_SECRET=
DARAJA_LIVE_PASS_KEY=
DARAJA_LIVE_BUSINESS_SHORT_CODE=4091271
DARAJA_LIVE_ACCESS_URL=<https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials>
DARAJA_LIVE_STKPUSH_URL=<https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest>
DARAJA_LIVE_STKPUSH_QUERY_URL=<https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query>
DARAJA_LIVE_C2B_REGISTER_URL=<https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl>

## ting test configs

TINNG_ACCESS_KEY=key
TINNG_ACCESS_SECRET=secret

## elastic configs

ELASTIC_USERNAME = username
ELASTIC_PASSWORD = pass

KIBANA_ELK_USER = kibana_system
KIBANA_ELK_PASSWORD = pass
