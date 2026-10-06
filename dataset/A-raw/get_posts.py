import requests
import json
from datetime import datetime, timedelta
from tqdm import tqdm
from argparse import ArgumentParser
import traceback
import logging
import os
import time

def get_args():
    parser = ArgumentParser()
    parser.add_argument('--search-query', '-q', type=str, default='covid')
    parser.add_argument('--start-time', '-s', type=str, default='2020-05-01', help='YYYY-mm-dd')
    parser.add_argument('--end-time', '-e', type=str, default='2020-05-15', help='YYYY-mm-dd')
    parser.add_argument('--num-datapoints', '-n', type=int, default=999)
    parser.add_argument('--output-dir', '-d', type=str, default='./')
    return vars(parser.parse_args())

def get_response(query, after, before, size, **kwargs):
    url = "https://api.pushshift.io/reddit/search/submission/"
    params = {
        "q": query,
        # "title": True, # PushShift bug: once set it to True, the PushShift database query will change to "True"...
        "after": after,
        "before": before,
        "size": size,
        "metadata": True,
        # "sort": {"created_utc": "asc"}, # IGNOREING asc trying to circumvent PushShift's asc bug, but couldn't...
        "sort": "created_utc" # desc by default..
    }
    try:
        request = requests.get(url, params=params)
        request.raise_for_status()
        request = request.json()
        # print(request.keys()) # dict_keys(['data', 'error', 'metadata'])
        request_data = request["data"]
        # request_error = request["error"]
        # print("request_error:", request_error)
        # request_metadata = request["metadata"]
        # print(json.dumps(request_metadata, indent=2))
        print(len(request_data))
        earliest_epo_int = after if len(request_data) < size//2 else int(request_data[-1]["created_utc"])
        print("Setting next before to:", datetime.fromtimestamp(earliest_epo_int))
        return request_data, earliest_epo_int
    except requests.exceptions.RequestException as err:
        print("ERROR CODE:", err.response.status_code)
        print("sleep 1 min and try again..")
        time.sleep(60) # try once more in _ secs
        return get_response(query, after, before, size)
    except Exception as err:
        logging.error(traceback.format_exc())
        raise SystemExit(err)

def post_filter(post, should_not_before, shoud_not_after):
    if post["over_18"]:
        return None
    if float(post["created_utc"]) < should_not_before or float(post["created_utc"]) > shoud_not_after:
        return None
    if post["removed_by_category"]:
        return None
    if "post_hint" in post:
        if post["post_hint"] == "image" or "video" in post["post_hint"]:
            return None
    # check domains
    if post["subreddit"] in post["domain"]: # no links
        return None
    return post

def main(output_dir, start_time, end_time, search_query, num_datapoints, **kwargs):
    start = datetime.strptime(start_time, '%Y-%m-%d')
    end = datetime.strptime(end_time, '%Y-%m-%d')
    span = end - start
    output_filenames = [os.path.join(output_dir, (start + timedelta(days=i)).strftime('%Y-%m-%d')+".jsonl") for i in range(span.days)]
    daily_start_end_int_query = [
            (int((start + timedelta(days=i)).timestamp()), int((start + timedelta(days=i+1)).timestamp())) 
        for i in range(span.days)]

    for out_fn, (start_epo_int, end_epo_int) in tqdm(zip(output_filenames, daily_start_end_int_query)):
        with open(out_fn, 'a') as writer:
            new_before_epo_int = end_epo_int
            while new_before_epo_int > start_epo_int:
                posts, new_before_epo_int = get_response(query=search_query, after=start_epo_int, before=new_before_epo_int, size=num_datapoints)
                for post in posts:
                    if post_filter(post, start_epo_int, end_epo_int):
                        json.dump(post, writer)
                        writer.write('\n')
                print(datetime.fromtimestamp(new_before_epo_int))

if __name__ == "__main__":
    main(**get_args())