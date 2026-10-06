import os
import json
import newspaper
import time


config = newspaper.Config()
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0'
config.browser_user_agent = user_agent

# query = 'covid'
query = 'coronavirus'
in_dirs = [os.path.join(f'../praw/{query}', month) for month in os.listdir(f'../praw/{query}')\
           if os.path.isdir(os.path.join(f'../praw/{query}', month))]
out_dir = f"./{query}/"

if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

reddit_domain = ['reddit.com', 'i.redd.it', 'v.redd.it', 'old.reddit.com', 'np.reddit.com']

chance = 3

for in_dir in in_dirs:
    files = sorted([file for file in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, file))])
    for file in files:
        print(file[:10])
        if not os.path.isdir(out_dir + file[:7]):
            os.mkdir(out_dir + file[:7])
        with open(os.path.join(in_dir, file), 'r', encoding='utf8') as reader, \
                open(os.path.join(out_dir+file[:7], file), 'a', encoding='utf8') as writer:
            for line in reader:
                data = json.loads(line)
                url = data['url']
                domain = data['domain']
                title = None
                content = None
                if data['domain'] in reddit_domain or domain[:5] == "self.":
                    continue
                for _ in range(chance):
                    try:
                        article = newspaper.Article(url=data['url'], config=config)
                        article.download()
                        article.parse()
                        title = article.title
                        content = article.text
                        json.dump({
                            'submission_id': data['id'],
                            'url': data['url'],
                            'domain': data['domain'],
                            'submission title': data['title'],
                            'news title': title,
                            'news content': content
                        }, writer)
                        writer.write('\n')
                        break
                    except newspaper.article.ArticleException:
                        print(f'Retrieve error for submission {data["id"]}, sleep 1sec and retry')
                        time.sleep(1)
                        continue
                    except Exception as e:
                        print(f'Retrieve error for submission {data["id"]}, sleep 1sec and retry')
                        time.sleep(1)
                        continue