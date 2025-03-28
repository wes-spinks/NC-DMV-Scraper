NC-DMV-Scraper is a tool you can use to become aware of DMV appointments right when they become available, without all the extra work of constantly manually monitoring the DMV website.

![example](exampleoutput.png)

It uses selenium to scrape appointment locations, dates, and times, from https://skiptheline.ncdot.gov/.


In order to set it up, you must first install python, selenium, and the selenium geckodriver

https://www.python.org/downloads/
https://pypi.org/project/selenium/
https://github.com/mozilla/geckodriver/releases

Then, you need to get the file path for the geckodriver you downloaded, and put it in scrapedmv.py like this:

GECKODRIVER_PATH = '/home/tommy/.cache/selenium/geckodriver/linux64/0.35.0/geckodriver' # Replace with your geckodriver path

Your format will depend on your operating system, e.g. on windows it may be like GECKODRIVER_PATH = 'C:\Users\tommy\Downloads\0.35.0\geckodriver' or something like that. 


Then, you need to go to discord, and create a webhook in a server you own ( make a server if you dont have one )
You can do that by going to the server, right clicking a channel -> edit channel -> integrations -> webhooks -> new webhook -> copy webhook url

Then put that webhook url in your scrapedmv.py like this:

YOUR_DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/10920931091/-JAOIFJWjenirieojOAJOIWjonfrreywoijojwojoOIAJODAab3" # !!! REPLACE WITH YOUR ACTUAL WEBHOOK URL !!!

( that is not a real webhook url to be clear ) 


Then, you just run `python3 scrapedmv.py`, and every 5 minutes or so it will start the scraping process. 
