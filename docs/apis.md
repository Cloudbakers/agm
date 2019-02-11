# Documentation for specific APIs

AGM is just a wrapper around the Google APIs, so in most cases you can refer to the API documentation for whatever service you're using. However, we've documented a few helpful notes and common commands for working with specific APIs.

## Admin SDKs

Get all user emails across a G Suite instance:

```
agm directory users list \
  -u [admin user] \
  --customer my_customer | 
jq -r .response.users[].primaryEmail
```

## Drive

TBD

