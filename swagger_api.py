# ...
import datetime
from datetime import timezone
from feedgen.feed import FeedGenerator
from flask import make_response
from flask import Flask, request, render_template
from random import randint

# ...

app = Flask(__name__)


def generate_news():
    news = []
    for i in range(15):
        item = {'title': f"Заголовок {randint(100, 1000)}",
                'url': f"http://news{randint(100,1000)}.com",
                'content': f"3333{randint(100,1000)}",
                'id': i + 1,
                'date': datetime.datetime.now(timezone.utc)
                }
        news.append(item)
    return news

def generate_events():
    events = []
    for i in range(10):
        item = {'title': f"Событие {randint(100, 1000)}",
                'url': f"http://event{randint(100,1000)}.com",
                'content': f"Cool event{randint(100,1000)}",
                'id': i + 1,
                'date': datetime.datetime.now(timezone.utc)
                }
        events.append(item)
    return events


@app.route('/swagger')
def rss():
    fg = FeedGenerator()
    fg.title('Feed title')
    fg.description('Feed description')
    fg.link(href='http://news.com')
    print(generate_news())
    for article in generate_news():  # get_news() returns a list of articles from somewhere
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['url'])
        fe.description(article['content'])
        # fe.guid(article['id'], permalink=False)  # Or: fe.guid(article.url, permalink=True)
        fe.pubDate(article['date'])

    response = make_response(fg.rss_str())
    response.headers.set('Content-Type', 'application/rss+xml')

    return response


# @app.route('/swagger/events')
# def get_events():
#     fg = FeedGenerator()
#     fg.title('Feed events')
#     fg.description('Events description')
#     fg.link(href='http://events.com')
#     print(generate_news())
#     for article in generate_events():  # get_news() returns a list of articles from somewhere
#         fe = fg.add_entry()
#         fe.title(article['title'])
#         fe.link(href=article['url'])
#         fe.description(article['content'])
#         # fe.guid(article['id'], permalink=False)  # Or: fe.guid(article.url, permalink=True)
#         fe.pubDate(article['date'])
#
#     response = make_response(fg.rss_str())
#     response.headers.set('Content-Type', 'application/rss+xml')
#
#     return response


if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1')
