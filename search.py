from googleapi import google
from googleapi.modules.utils import get_html
from bs4 import BeautifulSoup
import pandas as pd
from urllib.error import HTTPError
import time
import sys
import json
import argparse
import tqdm.auto as tqdm

headers = {
    "apikey": "2492a048-e435-4a19-8bd7-57c8e35cce78"
}


def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, num=15, **kwargs).execute()
    return res


def search(text, time_dur, num_page=3):
    '''
    query = {
        "q": text,
        "hl": "en",
        "num": 20
    }
    #
    url = f"https://api.goog.io/v1/search/" + urllib.parse.urlencode(query)

    resp = requests.get(url, headers=headers)
    search_results = resp.json()['results']

    time.sleep(max(90 - time_dur, 1))
    search_results = google_search(text, 'AIzaSyDCG-ss713pO2DNCO6QV39UBsRxfAjh7ss', 'ee7e31872ef041a02')

    '''
    search_results = google.search(text, num_page, time_dur=time_dur)
    print(text)
    if len(search_results) == 0:
        exit(1)
    kb = list()

    for result in search_results:

        sents = result.description
        if not sents:
            continue
        if ' — ' in sents:
            sents = sents.split(' — ')[1]

        missing = False
        if '...' in sents or '.' not in sents:
            missing = True

        sents = sents.replace('’', '\'')
        sents = sents.replace(' ', ' ')
        sents = sents.replace(' ...', '.')
        sents = sents.split('.')[:-1]
        for sent in sents:
            if sent:
                while sent.startswith(' '):
                    sent = sent[1:]

        knowledge = ''

        if not missing:
            for sent in sents:
                if sent:
                    knowledge += sent + '. '
            knowledge = knowledge[:-1]
            if knowledge and knowledge not in kb:
                kb.append(knowledge)

        html = None
        if len(kb) < 10 and missing:
            html = get_html(result.link, google=False)
        if html:
            try:
                soup = BeautifulSoup(html, "html.parser")
            except HTTPError as e:
                print('Cannot parsing', result.link)
                print(e)
                if e.code == 503:
                    print("503 Error: service is currently unavailable.")
                continue
            except Exception as e:
                print('Cannot parsing', result.link)
                print(e)
                continue
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            text = text.replace(' ', ' ')
            text = text.replace('’', '\'')
            if '�' in text or 'P@' in text:
                continue
            for sent in sents:
                if sent:
                    start = text.find(sent)
                    if start != -1:
                        end = text.find('. ', start)
                        if end != -1:
                            full_sent = text[start:end] + '. '
                            knowledge += full_sent
            if knowledge and knowledge not in kb:
                kb.append(knowledge)

    return kb


if __name__ == '__main__':
    '''
    kb = search('What sport is this? rugby', time_dur=90)
    for k in kb:
        print(k)
    '''
    parser = argparse.ArgumentParser()
    # Add parseargs
    parser.add_argument("--ques", default=3000)
    parser.add_argument("--pred", default=0)
    parser.add_argument("--end", default=-1)
    args = parser.parse_args()

    with open('see_predict.json', 'r') as f:
        qlist = json.load(f)

    count = int(args.ques)
    if int(args.end) !=-1:

        qlist = qlist[count:int(args.end)]
    else:
        qlist = qlist[count:]
    print(len(qlist))
    pd.set_option('display.max_colwidth', None)
    DF = pd.DataFrame(columns=['qid', 'question', 'answer', 'knowledge', 'gold'])
    DF.to_csv('test_cap1.csv', mode='a')
    predid = int(args.pred)
    time1 = time.time()
    for item in tqdm.tqdm(qlist):
        print('ques:', count)
        count += 1
        '''
        labels = list()
        for label in item['label'].keys():
            if item['label'][label] == 1:
                labels.append(label)
        if not labels:
            labels = list(item['label'].keys())
        '''
        labels = item['pred']
        if count == int(args.ques) + 1:
            labels = labels[predid:]
        for label in labels:
            print('pred:', predid)
            predid += 1
            q = item['sent'] + ' ' + label
            time2 = time1
            time1 = time.time()
            kb = (search(q, time1 - time2))
            for i in range(len(kb)):
                DF.at[i] = item['question_id'], item['sent'], label, kb[i], ''
            DF.to_csv('test_cap1.csv', mode='a', header=False)
            DF = DF.drop(index=DF.index)
        predid = 0

