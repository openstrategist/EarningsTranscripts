import os
import pandas as pd
import pickle
from processtext.util import process_text, remove_html_tag, extract_sessions

if __name__ == '__main__':

    inpath = '//Users//queenyc//Documents//Pyprojects//mdatopics//sa//'
    outpath = '//Users//queenyc//Documents//Pyprojects//mdatopics//data//'
    df = pd.DataFrame()

    for idx, filename in enumerate(os.listdir(inpath)):
        filepath = os.path.join(inpath+filename)
        if (filename[-3:] == 'csv') | (filename == '.DS_Store'):
            continue

        # extract data from earnings call script
        f = open(filepath)
        raw_text = f.read()
        clean_text = remove_html_tag(raw_text)
        lines = clean_text.splitlines()
        try:
            ticker, date, exchange, pre_start, qna_start, analyst_list, mgmt_list = extract_sessions(lines)
        except:
            continue

        #check date
        # if date < datetime(2010, 1, 1) | date > datetime(2030, 1, 1):
        #     continue

        # clean and process text
        remove_text_list = ['OPERATOR', 'THANK YOU', 'GOOD DAY', 'GOOD MORNING', 'QUESTION-AND-ANSWER SESSION', 'LADIES AND GENTLEMEN']
        remove_text_list = remove_text_list + analyst_list + mgmt_list
        text_pre = process_text(lines[pre_start:qna_start], remove_text_list)
        text_qna = process_text(lines[qna_start:], remove_text_list)

        # append outputs
        df.loc[idx, 'date'] = date
        df.loc[idx, 'ticker'] = ticker
        df.loc[idx, 'exch'] = exchange
        df.loc[idx, 'analyst'] = ', '.join(analyst_list)
        df.loc[idx, 'mgmt'] = ', '.join(mgmt_list)
        df.loc[idx, 'text_pre'] = ' '.join(text_pre)
        df.loc[idx, 'text_qna'] = ' '.join(text_qna)

        print('{} {} done'.format(idx, filename))

    with open(outpath+'transcript_processed.pickle', 'wb') as handle:
        pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)
