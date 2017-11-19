import os
import requests
import gzip
import shutil

from bs4 import BeautifulSoup

CA_SCHOOL_DISTRICTS_URL = 'https://transparentcalifornia.com/agencies/salaries/school-districts'
CSV_DOWNLOAD_URL = 'https://transparentcalifornia.com/export/school-districts/{county_abbr}/{agency_abbr}-{year}.csv'
OUTPUT_DIR = 'data'
RES_FILE = 'data.csv'


def download_file(url, filename):
    r = requests.get(url, verify=False, timeout=15)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            print 'Storing data into {filename}'.format(filename=filename)
            f.write(r.content)
    else:
        print 'Error downloading file from {url}'.format(url=url)


def fetch_files():
    s = requests.Session()
    r = s.get(url=CA_SCHOOL_DISTRICTS_URL,
              verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')

    main_div = soup.find("div", {"class": "span9"})

    county_names = [c.text for c in main_div.findAll("h2")]
    county_tables = main_div.findAll("table")

    idx = 0
    files_cnt = 0
    counties_arr = []

    COL_COUNTY_ABBR = 4
    COL_AGENCY_ABBR = 5

    for t in county_tables:
        county_name = county_names[idx]
        agencies_trs = t.findAll("tr")
        county_abbr = agencies_trs[0].findAll("td")[0].find("a")['href'].split('/')[COL_COUNTY_ABBR]
        agencies_arr = []
        for atr in agencies_trs:
            agencies_tds = atr.findAll("td")
            ca_base = agencies_tds[0].find("a")
            agency_name = ca_base.text
            try:
                ca_parts = ca_base['href'].split('/')
                agency_abbr = ca_parts[COL_AGENCY_ABBR]
            except Exception as e:
                print 'Error parsing URL: {url}'.format(url=ca_base['href'])
                continue

            years = [x.text for x in agencies_tds[1].findAll("a")]
            files_cnt += len(years)
            agencies_arr.append({'name': agency_name,
                                 'abbr': agency_abbr,
                                 'years': years})
        counties_arr.append({'name': county_name,
                             'abbr': county_abbr,
                             'agencies': agencies_arr})
        idx += 1

    idx = 1
    for c in counties_arr:
        for a in c['agencies']:
            for y in a['years']:
                print 'Downloading file {idx} of {files_cnt}'.format(idx=idx, files_cnt=files_cnt)
                url = CSV_DOWNLOAD_URL.format(county_abbr=c['abbr'],
                                              agency_abbr=a['abbr'],
                                              year=y)
                filename = '{output_dir}/{county_name}_{agency_name}_{year}.csv'.format(output_dir=OUTPUT_DIR,
                                                                                        county_name=c['name'],
                                                                                        agency_name=a['name'],
                                                                                        year=y)
                download_file(url, filename)
                idx += 1


def gen_res_file(source_files_dir, res_file_path):
    src_files = [fn for fn in os.listdir(source_files_dir)]
    src_files_cnt = len(src_files)
    csv_header = 'County,Employee Name,Job Title,Base Pay,Overtime Pay,Other Pay,Benefits,Total Pay,Total Pay & Benefits,Year,Notes,Agency,Status\n'
    with open(res_file_path, 'w') as res_f:
        res_f.write(csv_header)
        idx = 1
        for src_file in src_files:
            print 'Processing file {idx} of {src_files_cnt}'.format(idx=idx, src_files_cnt=src_files_cnt)
            county_name = src_file.split('_')[0]
            f_path = os.path.join(source_files_dir, src_file)
            with open(f_path, 'r') as cur_f:
                rows = [r for r in cur_f]
                for r in rows[1:]:
                    res_f.write(county_name + ',' + r)
            idx += 1
    print 'Compressing resulting file...'
    with open(res_file_path, 'rb') as f_in, gzip.open('{res_file_path}.gz'.format(res_file_path=res_file_path),
                                                      'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)


if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    fetch_files()

if not os.path.exists(RES_FILE):
    gen_res_file(OUTPUT_DIR, RES_FILE)



# print county_names
# print county_tables

