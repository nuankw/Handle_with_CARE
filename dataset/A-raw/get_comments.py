from argparse import ArgumentParser
import json
import praw
import time
import os
from os.path import join

reddit_ids = json.load(open("./reddit_ids.json"))
reddit = praw.Reddit(
    client_id = reddit_ids["client_id"],
    client_secret = reddit_ids["client_secret"],
    user_agent = reddit_ids["user_agent"],
)

def get_args():
    parser = ArgumentParser()
    parser.add_argument("--input_dirpath",      "-i", type=str, default="../../collected/pushshift/covid/mar")
    parser.add_argument("--output_dirpath",     "-o", type=str, default="../../collected/praw/covid/mar")
    parser.add_argument("--needed_fields",      "-f", type=str, nargs='+',)
    parser.add_argument("--minimum_comments",   "-c", type=int, default=10)
    return vars(parser.parse_args())


def check_post(post, min_cmts=10):
    if post["num_comments"] >= min_cmts:
        domain = post["domain"]
        return True
    return False

def filter_post(post, needed_fields):
    return {k: post[k] if k in post else "RETRIEVING_ERROR" for k in needed_fields}

def get_comment_timeline(post, attempts=0):
    try:
        try:
            subreddit = reddit.subreddit(post["subreddit"])
            subreddit.quaran.opt_in()
            print("subreddit quarantine lifted for comment access")
        except:
            pass
        submission = reddit.submission(post["id"])
        submission.comments.replace_more(limit=20)
        all_comments = {}
        for cmt in submission.comments.list():
            all_comments[cmt.created_utc] = {
                "id": cmt.id,
                "author_name": cmt.author.name if cmt.author else "RETRIEVING_ERROR",
                "parent_id": cmt.parent_id, # The ID of the parent comment (prefixed with t1_). If it is a top-level comment, this returns the submission ID instead (prefixed with t3_).
                "created_utc": cmt.created_utc,
                "body": cmt.body,
                "score": cmt.score
            }
        all_comments = [cmt for _, cmt in sorted(all_comments.items())]
        return all_comments
    except:
        if attempts == 0:
            print("trying to retrieve comments again for post:", post["permalink"])
            time.sleep(20)
            return get_comment_timeline(post, attempts=attempts+1)
        else:
            print("Error retrieving comments from post:", post["permalink"])
            return None

def main(**kwargs):
    input_jsonlfiles = sorted([os.path.join(kwargs["input_dirpath"],f) for f in os.listdir(kwargs["input_dirpath"]) if os.path.isfile(join(kwargs["input_dirpath"], f))])
    output_jsonlfiles = sorted([os.path.join(kwargs["output_dirpath"],f) for f in os.listdir(kwargs["input_dirpath"]) if os.path.isfile(join(kwargs["input_dirpath"], f))])
    if not os.path.isdir(kwargs["output_dirpath"]):
        os.makedirs(kwargs["output_dirpath"])
    
    for infile, outfile in zip(input_jsonlfiles, output_jsonlfiles):
        print("Procecssing {} ...".format(infile))
        with open(infile) as inf, open(outfile, "a") as outf:
            for i, line in enumerate(inf):
                post = json.loads(line)
                if check_post(post, kwargs["minimum_comments"]):
                    print("Currently processing line {}".format(i+1))
                    timeline_cmt_list = get_comment_timeline(post)
                    if timeline_cmt_list:
                        filtered_post = filter_post(post, kwargs["needed_fields"])
                        filtered_post.update({
                            "comment timeline": timeline_cmt_list # I wish I typed "comment_timeline", sorry!
                        })
                        json.dump(filtered_post, outf)
                        outf.write('\n')


if __name__ == "__main__":
    main(**get_args())