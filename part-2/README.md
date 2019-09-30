# Getting Started With Connect Part 2

## How to build
`pipenv install`

## How to run

1. Run `ngrok http 5000`. Make note of the url `ngrok` generated. Look for a line that looks like this `Forwarding         https://123de333.ngrok.io -> http://localhost:5000`. In this case the url is `https://123de333.ngrok.io`. 
1. Go to [your service API page](https://platform.ifttt.com/mkt/api). Set the url to the one `ngrok` generated. Save the changes. Use the values from this page in the next step.
1. Open a second terminal window and run
   ```
   export IFTTT_SERVICE_URL=<service-url> # ngrok url
   export IFTTT_SERVICE_KEY=<service-key> # your secret key
   pipenv run flask run
   ```
