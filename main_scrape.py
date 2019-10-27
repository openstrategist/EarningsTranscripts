import subprocess

for n_page in range(0, 6000):
    subprocess.call(['python', 'scraper/scrape_earnings_transcript.py', str(n_page)])
    print('finished getting page ', n_page)
