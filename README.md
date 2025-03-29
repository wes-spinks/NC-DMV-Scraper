NC-DMV-Scraper is a tool you can use to become aware of DMV appointments right when they become available, without all the extra work of constantly manually monitoring the DMV website.

![example](exampleoutput.png)

It uses selenium to scrape appointment locations, dates, and times, from https://skiptheline.ncdot.gov/.

I strongly recommend you set it up yourself, but if you are entirely unwilling to do that ( even though it is quite easy ), you could reach out to me ( tommy092464_62746 on discord, or via github issues ) and pay me like 5 bucks and ill host it for you for however long you need, with absolutely no uptime gurantees ( e.g. if my power, or internet go out, that sucks for you. ). 

In order to set it up, you must first install python, selenium, and the selenium geckodriver

https://www.python.org/downloads/

https://pypi.org/project/selenium/

https://github.com/mozilla/geckodriver/releases

Then, download the code for this by clicking the green code button in the top right, and clicking download zip. Open that zip up, and extract it somewhere.

Then, you need to get the file path for the geckodriver you downloaded, and put it in scrapedmv.py like this:

```python
GECKODRIVER_PATH = '/home/tommy/.cache/selenium/geckodriver/linux64/0.35.0/geckodriver' # Replace with your geckodriver path
```

Your format will depend on your operating system, e.g. on windows it may be like `GECKODRIVER_PATH = 'C:\Users\tommy\Downloads\0.35.0\geckodriver'` or something like that. 


Then, you need to go to discord, and create a webhook in a server you own ( make a server if you dont have one )
You can do that by going to the server, right clicking a channel -> edit channel -> integrations -> webhooks -> new webhook -> copy webhook url

Then put that webhook url in your scrapedmv.py like this:

```python
YOUR_DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/10920931091/-JAOIFJWjenirieojOAJOIWjonfrreywoijojwojoOIAJODAab3" # !!! REPLACE WITH YOUR ACTUAL WEBHOOK URL !!!
```

( that is not a real webhook url to be clear ) 

Then, you just run `python3 scrapedmv.py`, and every 5 minutes or so it will start the scraping process. 

Once you have this setup, there is also a lot of tweaking you can do, here are some examples:
* Currently, it will report all appointments from all locations to you, but that is not necessarily what you want
* you can restrict it to only a few locations that are within comfortable driving range of where you live, or walking range of where you live
* you can restrict it to only appointments in timeframes that you want ( e.g. i dont want to wait 3 months for an appointment, so i just waited until someone else's appointment for 3 days from now became available and snatched theirs up )
* you can make it scrape more, or less, often. The tradeoff being the annoyance of constant notifications vs the loss of potential opportunity to snatch up a nice appointment 

If you want help with any of those things, make a github issue and i will be glad to help out. They should be basic enough though that this is really a chatgpt-able problem.

If you do make changes like that, please publish them, so that others lives can also be easier!

#### Build and run the containerized application
Docker build

```bash
docker build -t nc-dmv-scraper .
```

Run Container
```bash
docker run -e YOUR_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/10920931091/-JAOIFJWjenirieojOAJOIWjonfrreywoijojwojoOIAJODAab3" nc-dmv-scraper
```

Run a pre-built image
```bash
docker run -e YOUR_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/10920931091/-JAOIFJWjenirieojOAJOIWjonfrreywoijojwojoOIAJODAab3" quay.io/vargav/nc-dmv-scraper
```
