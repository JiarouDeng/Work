#!/usr/bin/env python3

import cgi
import subprocess
import json
import sqlite3
import time


PATH_TO_MACHINE = "./etovucca"
PATH_TO_SQLITE = "./sqlite3"
PATH_TO_DB = "rtbb.sqlite3"
ID_SQL = 'SELECT id FROM Election WHERE deadline_day={} AND deadline_mon={} AND deadline_year={}'

def convert_date_to_id(date):
    # Please don't ever actually do this.
    date_positions = date.split("-")
    sql = ID_SQL.format(date_positions[2], date_positions[1], int(date_positions[0]) - 1900) # U+1F914
    election_id = int(subprocess.check_output([PATH_TO_SQLITE, PATH_TO_DB, sql]))
    return election_id


print("Content-Type: text/html")
print()
print('<link rel="stylesheet" href="https://spar.isi.jhu.edu/teaching/443/main.css">')
print('<h2 id="dlobeid-etovucca-voting-machine">DLOBEID EtovUcca Voting Machine</h2>')
print('<h1 id="vote">Vote</h1><br>')
form = cgi.FieldStorage(keep_blank_values=True)
try:
    json_elections = subprocess.check_output(
        [PATH_TO_MACHINE, "get-elections"]).decode('utf-8')
    elections = json.loads(json_elections)
    if len(form) != 0:
        ids = form.getvalue('election').split('_')
        unique_office_id = str(elections[ids[0]]['offices'][int(ids[1])]['id'])
        unqiue_candidate_id = str(elections[ids[0]]['offices'][int(ids[1])]['candidates'][int(ids[2])]['id'])
        conn = sqlite3.connect(PATH_TO_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Vote WHERE voter=? AND office=?", (form.getvalue('voterId'), unique_office_id))
        vote_count = cursor.fetchone()[0]

        if vote_count == 0:
            time.sleep(5) 
            try:
                cursor.execute("INSERT INTO Vote (voter, candidate, office) VALUES (?, ?, ?)", 
               (form.getvalue('voterId'), unqiue_candidate_id, unique_office_id))

                conn.commit()
                print('<b>Successfully cast ballot.</b>')
            except sqlite3.IntegrityError:
                print('<b>Error: You have already voted for this office.</b>')
                
        else:
            print('<b>Error: You have already voted for this office.</b>')

        conn.close()
    else:
        print('<form method="post">')
        print('<label for="voterId">Voter ID</label><br>')
        print('<input type="number" id="voterId" name="voterId"><br>')
        print('<label for="election">Ballot</label><br>')
        print('<select name="election" id="election">')
        for date in elections:
            if elections[date]['status'] == "open":
                for oid in range(0, len(elections[date]['offices'])):
                    office = elections[date]['offices'][oid]
                    print('<optgroup label="{}: {}">'.format(
                        date, office['name']))
                    for cid in range(0, len(office['candidates'])):
                        candidate = office['candidates'][cid]
                        print(
                            '<option value="{}_{}_{}">{}</option>'.format(date, oid, cid, candidate['name']))
                    print('</optgroup>')
        print('</select>')
        print('<input type="submit" value="Vote">')
        print('</form>')
except subprocess.CalledProcessError as e:
    print('<b>Error with ballot:</b>')
    print('<code>')
    print(e.output.decode('utf-8'), end="")
    print('</code>')
except Exception as e:
    print('<b>Error with ballot:</b>')
    print('<code>')
    print(e)
    print('</code>')
print('<br><a href="./home.cgi">Return to Homepage</a>')
