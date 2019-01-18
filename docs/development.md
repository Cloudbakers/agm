# Development

AGM tries to follow the Unix principle of [Do One Thing and Do It Welll](https://en.wikipedia.org/wiki/Unix_philosophy#Do_One_Thing_and_Do_It_Well). This means things like parsing JSON output, converting to CSVs or uploading results to a Google Sheet, etc are not part of AGM. There are other great tools that you can use with AGM to accomplish these tasks. I want to keep this codebase as simple and focused as possible. I also don't want to build out functionality that caters to a specific API, ie some extra Google Drive features. The behavior of AGM should be as transparent as possible and deviate from what it would look like to make a curl request to the Google API as little as possible. There are very minor changes I make (such as setting a default fields value of \*), but these changes should be limited in scope and easy to override.

I would love help with refactoring, documentation, QA, and adding tests. 

