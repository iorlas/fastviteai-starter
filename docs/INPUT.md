I think we got things overengineered

We want to have 2 pipelines which I can run:

Watchers - will take data from monitoring_list.txt. Will use different kids of watchers (youtube, subreddits, rss, hackernews) to extract links. Triggered manually or every 6 hours.


Manual URLs - will take the data from manual_links.txt directly. Manually triggered.


When we have links (directly from manual urls, or extracted from watchers), we want to extract HTML, clean it up, summarize.

Use medallion architecture, runnable locally only, no deployment necessary. Plan that I will rerun both pipelines easily, so we need to avoid duplicated work - like we have to cache html pages and summarizations. Potentially I will remove summations to improve it's quality, then will rerun it - so HTML pages should be reused.

What I like so far:
- UI
- Summation module (in core)
- Experiments
- IO Managers looks interesting

I feel like we need to simplify orchestration a lot, I don't like:
- Sensors waiting
- Too many separate runs so I struggle to see what is going on