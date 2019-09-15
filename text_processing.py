import re
from datetime import datetime
import os
import pandas as pd
import numpy as np
from nltk.stem import WordNetLemmatizer
import string
import pickle


def remove_html_tag(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

def extract_date(text):
    flag, year = 0, 0
    words = text.replace(',', ' ').lower().split()
    month_dict = {'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6
        , 'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
    for k, v in month_dict.items():
        if k in words:
            flag = 1
            mon = v
            mon_pos = words.index(k)
            day = int(words[mon_pos + 1])
            year = int(words[mon_pos + 2])
            break
    if (flag == 0) | (year==0):
        return None
    else:
        return datetime(year, mon, day)

def process_text(x, remove_text_list):
    # format
    x = ' '.join(x).upper()
    #remove words
    for word in remove_text_list:
        x = x.replace(word, '')
    #remove punctuation
    remove = dict.fromkeys(map(ord, '\n ' + string.punctuation))
    x = [ word.translate(remove) for word in x.split()]
    if '' in x:
        x.remove('')
    # lemmatize
    lemmatizer = WordNetLemmatizer()
    x = [lemmatizer.lemmatize(word) for word in x]
    return x


def extract(lines, DATE_MAX_SIZE=5, HEADER_MAX_SIZE=50):

    # params
    section_line_mgmt = ['Executives', 'Company Participants', 'Corporate Participants']
    section_line_analysts = ['Analysts', 'Conference Call Participants']
    section_line_presentation = ['Presentation', 'Operator']
    section_line_qna = ['Question-and-Answer Session']
    DATE_MAX_SIZE = 5  # the line that includes date should be less than 5
    HEADER_MAX_SIZE = 50  # the header of the script should be less than 50 lines

    # initialize
    cur_line = 0
    presentation_start_line = -1
    qna_start_line = -1
    mgmt_list = []
    analyst_list = []
    qna = []

    # extract ticker in first line
    p1 = lines[0].find('(')
    p2 = lines[0].find(':')
    p3 = lines[0].find(')')
    if p1 == -1 or p2 == -1 or p3 == -1:
        print('wrong format: ', lines[0])
    else:
        exchange = lines[0][p1 + 1:p2]
        ticker = lines[0][p2 + 1:p3]

    # Extract date
    for i in range(len(lines)):
        release_date = extract_date(lines[i])
        if release_date is not None:
            cur_line = i + 1
            break
    if cur_line > DATE_MAX_SIZE:
        return np.nan

    # detect management section
    for i in range(cur_line, len(lines)):
        if lines[i] in section_line_mgmt:
            cur_line = i + 1
            break
    if cur_line > HEADER_MAX_SIZE:
        return np.nan

    # build management list
    for i in range(cur_line, len(lines)):
        p = lines[i].find(' - ')  # - within a name doesn't have leading/trailing spaces
        if p == -1:
            cur_line = i
            break
        else:
            mgmt_list.append(lines[i][0:p].strip().upper())
    if cur_line > HEADER_MAX_SIZE:
        return np.nan

    # build analyst list
    for i in range(cur_line, len(lines)):
        if lines[i] in section_line_analysts:
            cur_line = i + 1
            break
    if cur_line > HEADER_MAX_SIZE:
        return np.nan
    for i in range(cur_line, len(lines)):
        p = lines[i].find(' - ')
        if p == -1:
            cur_line = i
            break
        else:
            analyst_list.append(lines[i][0:p].strip().upper())
    if cur_line > HEADER_MAX_SIZE:
        return np.nan

    # detect presentation section
    for i in range(cur_line, len(lines)):
        if lines[i] in section_line_presentation:
            presentation_start_line = i
            cur_line = i + 1
            break
    if presentation_start_line == -1:
        return np.nan

    # detect Q&A section
    for i in range(cur_line, len(lines)):
        if lines[i] in section_line_qna:
            qna_start_line = i
            cur_line = i + 1
            break
    if qna_start_line == -1:
        return np.nan

    # build Q&A content
    str = ''
    for i in range(cur_line, len(lines)):
        if i == len(lines) - 1:
            str = str + lines[i] + '\n'
            qna.append(str)
        elif lines[i].strip().upper() == 'OPERATOR':
            # start a new question
            if len(str) > 0:
                qna.append(str)
            str = lines[i] + '\n'  # refresh str
        else:
            str = str + lines[i] + '\n'

    return ticker, release_date, exchange, presentation_start_line, qna_start_line, analyst_list, mgmt_list



if __name__ == '__main__':

    inpath = '//Users//queenyc//Documents//Pyprojects//mdatopics//sa//'
    outpath = '//Users//queenyc//Documents//Pyprojects//mdatopics//data//'
    out = pd.DataFrame()
    idx = 0
    analyst, mgmt, pre, qna = {}, {}, {}, {}

    for filename in os.listdir(inpath):
        idx += 1
        filepath = os.path.join(inpath+filename)
        if (filename[-3:] == 'csv') | (filename == '.DS_Store'):
            continue

        # extract data from earnings call script
        f = open(filepath)
        raw_text = f.read()
        clean_text = remove_html_tag(raw_text)
        lines = clean_text.splitlines()
        try:
            ticker, date, exchange, pre_start, qna_start, analyst_list, mgmt_list = extract(lines)
        except:
            continue

        # clean text
        remove_text_list = ['OPERATOR', 'THANK YOU', 'GOOD DAY', 'GOOD MORNING', 'QUESTION-AND-ANSWER SESSION', 'LADIES AND GENTLEMEN']
        remove_text_list = remove_text_list + analyst_list + mgmt_list
        text_pre = process_text(lines[pre_start:qna_start], remove_text_list)
        text_qna = process_text(lines[qna_start:], remove_text_list)

        # append outputs
        out_i = pd.DataFrame({'date': [date], 'ticker': [ticker], 'exch': [exchange], 'idx': idx})
        out = pd.concat([out, out_i], axis=0)
        analyst[idx] = analyst_list
        mgmt [idx] = mgmt_list
        pre[idx] = text_pre
        qna[idx] = text_qna
        print('{} {} done'.format(idx, filename))

    with open(outpath+'transcript_processed.pickle', 'wb') as handle:
        pickle.dump([out, analyst, mgmt, pre, qna], handle, protocol=pickle.HIGHEST_PROTOCOL)