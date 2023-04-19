# Upload Scripts

This directory contains scripts that are used to upload data to the server.

## Blueprint

### Export / Import guide

1. Open the job, hit export and then subject data and images.
2. select your target folder and select data and images.
3. Select CSV format, comma seperator, quote, and header row, and then hit next.
4. Select at least these rows: Last Name, First Name, Subject ID(student ID), Internal ID, Grade, Images. Note: The order doesn't matter, but don't change the names of the rows. Then hit next.
5. Select primary image, make sure orginal file name is selected, and then hit export.
6. Follow the command line instructions to upload the data to the server. Ex: `python -m scripts.blueprint -h`
