# Requires jq: https://stedolan.github.io/jq/
# Requires json2csv: https://www.npmjs.com/package/json2csv or https://github.com/alexwennerberg/json2csv

# For all files, get file name, ID, and owner email address
agm drive files list --user $USERNAME | # replace with user
jq '.response.files[] | {name, id, owner: .owners[0].emailAddress}' |
json2csv # > ouptut.csv
