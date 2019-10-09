agm directory users list \
  -u [admin user] \
  --customer my_customer | 
jq -r .response.users[].primaryEmail
