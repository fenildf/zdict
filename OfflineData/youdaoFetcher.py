#!/usr/bin/env python
# coding=utf-8
import os
import time
import zipfile
import urllib2
import sqlite3
import re
import xml.dom.minidom

from pyquery import PyQuery


class WebFetcher:
    def __init__(self, database, word_list_file):
        self.database = database
        if os.path.exists(self.database):
            overwrite = raw_input('%s already exists, (R)ebuild or (U)pdate database, or (N)ot?' % self.database)
            if overwrite == 'r':
                self.createDB()
                self.initDB(word_list_file)
            if overwrite == 'u':
                self.initDB(word_list_file)
        else:
            self.createDB()
            self.initDB(word_list_file)
        self.conn = sqlite3.connect(self.database)
        self.query_count = 0

    def createDB(self):
        open(self.database, 'w').close()
        conn = sqlite3.connect(self.database)
        conn.execute(('CREATE TABLE `dict` (\n'
                      '             `word`\tTEXT NOT NULL UNIQUE,\n'
                      '             `read`\tINTEGER NOT NULL DEFAULT 0,\n'
                      '             `empty`\tINTEGER NOT NULL DEFAULT 0,\n'
                      '             `basic_ec`\tTEXT );'
        ))
        conn.close()

    def initDB(self, word_list_file):
        word_list = open(word_list_file)
        conn = sqlite3.connect(self.database)
        for line in word_list:
            word = line.strip()
            if word != '':
                sql_cmd = "INSERT OR IGNORE INTO dict (word) VALUES ('%s');" % word.replace("'", "''")
                conn.execute(sql_cmd)
        word_list.close()
        conn.commit()
        conn.close()

    def getDOM(self, word):
        url = 'http://dict.youdao.com/search?le=eng&q=%s&keyfrom=dict.top' % urllib2.quote(word, '')
        conn = urllib2.urlopen(url)
        html = conn.read()
        conn.close()
        self.dom = PyQuery(html)

    def getBasicEC(self):
        basic_ec_dom = self.dom('#phrsListTab')('.trans-container')
        if len(basic_ec_dom) == 0:
            return 0
        html = basic_ec_dom.html().encode('utf-8')
        html = re.sub(r'\s*\n\s*', r' ', html)  # delete redundant space before insert into database
        html = re.sub(r'<!--.*?-->', r'', html)
        html = re.sub(r'[\ \t]*([<>])[\ \t]*', r'\1', html)
        return html

    def updateDB(self, word, meaning):
        sql_cmd = "UPDATE dict SET read = 1, empty = 1 WHERE word = '%s';" % word.replace("'", "''")
        if meaning != 0:
            sql_cmd = "UPDATE dict SET read = 1, basic_ec = '%s' WHERE word = '%s';" % (
                meaning.replace("'", "''"), word.replace("'", "''"))
        self.conn.execute(sql_cmd)

    def queryWords(self):
        cursor = self.conn.execute("SELECT rowid, word FROM dict WHERE read = 0;")
        for row in cursor:
            self.query_count += 1
            word_id = row[0]
            word = row[1].encode('utf-8')
            print self.query_count, word_id, word
            try:
                self.getDOM(word)
            except urllib2.HTTPError, e:
                print '\t! HTTPError %i %s' % (e.code, e.reason)
                continue
            meaning = self.getBasicEC()
            if meaning == 0:
                print '\t! No meaning'
            self.updateDB(word, meaning)
            if self.query_count % 50 == 0:
                self.conn.commit()
                time.sleep(0.5)
            if word_id % 10000 == 0 and self.query_count > 1000:
                self.zipDB(self.database, '%s-%i.zip' % (self.database, word_id))
                time.sleep(5)
        self.conn.commit()
        self.zipDB(self.database, '%s.zip' % (self.database))

    def zipDB(self, infile, outfile):
        zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
        zip.write(infile)
        zip.close()

    def printHTML(self, html_file):
        cursor = self.conn.execute('SELECT word, basic_ec FROM dict WHERE read = 1 AND empty = 0;')
        xml_tmp = ['<dict>']
        for row in cursor:
            word = row[0].encode('utf-8')
            meaning = row[1].encode('utf-8')
            xml_tmp.append('<one><word>%s</word><meaning>%s</meaning></one>' % ( word, meaning))
        xml_tmp.append('</dict>')
        dic_xml = '\n'.join(xml_tmp)
        self.writeHTML(dic_xml, html_file)
        # pretty_xml = self.prettifyXML(dic_xml)
        # self.writeHTML(pretty_xml, 'pretty.html')

    def prettifyXML(self, ugly_xml):
        pretty_xml = xml.dom.minidom.parseString(ugly_xml).toprettyxml()
        xml_tmp = pretty_xml.encode('utf-8').split('\n')
        xml_tmp_no_blank = []
        for i in xml_tmp:
            if i.strip() != '':
                xml_tmp_no_blank.append(i)
        return '\n'.join(xml_tmp_no_blank)

    def writeHTML(self, xml, html_file):
        inf = open(html_file, 'w')
        inf.write('<!DOCTYPE html>\n<html>\n<meta charset="UTF-8">\n')
        inf.write(xml)
        inf.write('\n</html>')
        inf.close()


if __name__ == '__main__':
    web_dict = WebFetcher('youdao.db', 'words_mw11.txt')
    web_dict.queryWords()
    # web_dict.printHTML('youdao.html')
    web_dict.conn.close()
