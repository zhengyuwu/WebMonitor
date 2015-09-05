# coding=utf-8
__author__ = "zheng"

import urllib2
import chardet
import re
import urlparse
import time
import hashlib
import threading


class crawlLinks:
    def __init__(self):
        self.baseWebsMd5 = ''
        self.urls = {}
        # self.crawlLinks(baseUrl, self.urls)

    # 获取网站url列表
    def getBaseWebs(self):
        webs = {}
        try:
            with open('baseWebs.txt', 'r') as f:
                for line in f:
                    line = line.decode('gbk', 'ignore').strip('\r\n\t ')
                    if not line: continue
                    if line.startswith('#'):
                        continue
                    item = line.split('\t', 2)
                    if len(item) == 2:
                        item[2] = ''
                    if len(item) == 1:
                        print u'网站信息录入错误（baseWebs.txt）：%s' % line
                        continue
                    webs[item[0]] = [item[1], item[2]]
        except Exception, e:
            print u'Error: 文件baseWebs.txt操作失败'
            print e
            return 1
        return webs

    # 用于计算baseWebs.txt文件的md5值，若发生变更则需要执行网站链接抓取
    def calFileMd5(self, fileName):
        try:
            with open(fileName, 'r') as f:
                fileMd5 = hashlib.md5(f.read()).hexdigest()
        except Exception, e:
            print u'文件%s操作失败' % fileName
            return 1
        return fileMd5

    # 爬虫线程，读取baseWebs.txt中的网站，抓取网站链接保存到webs.txt文件中
    def startCrawl(self, sleep=3600):
        print u'====爬虫线程开始运行......'
        while True:
            if not self.baseWebsMd5:
                self.baseWebsMd5 = self.calFileMd5('baseWebs.txt')
                print u'====爬虫线程：首次运行，执行网站链接抓取'
                # 清空文件webs.txt
                with open('webs.txt', 'w') as f:
                    f.write('')
            elif self.calFileMd5('baseWebs.txt') == self.baseWebsMd5:
                print u'爬虫线程：baseWebs列表未发生改变，不需要执行网站链接抓取'
                print u'爬虫线程：挂起%s秒' % sleep
                time.sleep(sleep)
                continue
            else:
                print u'====爬虫线程：baseWebs列表发生改变，需要执行网站链接抓取'
                # 清空文件webs.txt
                with open('webs.txt', 'w') as f:
                    f.write('')
            baseWebs = self.getBaseWebs()
            for baseUrl in baseWebs.keys():
                webs = set()
                webs.add(baseUrl)
                print u'====爬虫线程：开始抓取[%s]所有页面的超链接，当前时间(%s)' % (baseUrl, time.strftime('%Y-%m-%d %H:%M:%S'))
                t = time.time()
                self.mulLinkSpider(baseUrl, self.urls, baseUrl, depth=1)
                print u'====爬虫线程：完成[%s]所有页面超链接的抓取，完成时间(%s)，历时%s(秒)' % (
                baseUrl, time.strftime('%Y-%m-%d %H:%M:%S'), time.time() - t)
                for url in self.urls:
                    if self.urls[url] == 0:
                        webs.add(url)
                with open('webs.txt', 'a') as f:
                    for url in webs:
                        text = url + '\t' + baseWebs[baseUrl][0] + '\t' + baseWebs[baseUrl][1]
                        f.write(text.encode('gbk', 'ignore') + '\r\n')
                        print u'====爬虫线程：写入链接[%s]到文件webs.txt中' % text
            # 首次运行或baseWebs.txt发送改变时，更新self.baseWebsMd5
            self.baseWebsMd5 = self.calFileMd5('baseWebs.txt')
            print ''

    # 抓取页面url中的链接，符合条件的放到字典self.urls中
    # baseUrl是从baseWebs.txt中读取的链接，用于限定抓取到的url在baseUrl的层级下
    # 参数depth用于控制线程数量
    def mulLinkSpider(self, url, urls, baseUrl, depth):
        print u'爬虫线程：开始多线程抓取页面[%s]上的链接，初始页面是[%s]' % (url, baseUrl)
        request = urllib2.Request(url)
        try:
            body = urllib2.urlopen(url=request, timeout=5).read()
        except Exception, e:
            print u'爬虫线程：页面[%s]访问错误，更新状态为1' % url
            urls[url] = 1
            return 1
        # 判断页面body的字符集
        charset = chardet.detect(body)['encoding']
        if not charset: charset = 'utf-8'
        body = body.decode(charset, 'ignore')
        # 抓取页面内容body中的链接
        # pattern = re.compile(r'(href=[\'\"](.*?)[\'\"])|([\'\"](http://.+?)[\"\'])')
        pattern = re.compile(r'(href|src)\s*=\s*[\'\"](.*?)[\'\"]', re.I)
        items = re.findall(pattern, body)

        # newUrlSet是从页面url中抓取到的链接的唯一集合
        newUrlSet = set()
        for item in items:
            # 对于相对url，补全路径
            url1 = urlparse.urljoin(url, item[1]).strip(' \r\n\t\"\'')
            # url2 = urlparse.urljoin(url, item[2]).strip(' \r\n\t\"\'')
            # 抓取的url限定在baseUrl的层级下，baseUrl是从baseWebs.txt中读取的url
            if url1.startswith(baseUrl): newUrlSet.add(url1)
            # if url2.startswith(baseUrl): newUrlSet.add(url2)

        threads = []
        for newUrl in newUrlSet:
            if urls.has_key(newUrl):
                continue
            print u'爬虫线程：成功抓取到链接[%s]，先记录状态为0' % newUrl
            urls[newUrl] = 0
            # 对新抓取到的链接进行递归调用
            # 参数depth用于控制线程数量
            if depth <= 1:
                threads.append(threading.Thread(target=self.mulLinkSpider, args=(newUrl, urls, baseUrl, depth + 1)))
            else:
                self.mulLinkSpider(newUrl, urls, baseUrl, depth)

        for thread in threads:
            print u'====爬虫线程：Thread %s [depth %s] start...' % (thread, depth)
            thread.start()

        for thread in threads:
            print u'====爬虫线程：Thread %s [depth %s] end...' % (thread, depth)
            thread.join()

        return 0


if __name__ == '__main__':
    # 可以运行该程序，只启动爬虫线程，抓取baseWebs.txt中网站所有页面的超链接，并保存在webs.txt中
    # 多线程爬虫，适用于网络延时较大的情况下
    crawl = crawlLinks()
    # 爬虫线程，参数为线程挂起时间（秒）
    # 如果不需要重新爬取baseWebs.txt中的网站所有页面的超链接，则不要启动该线程
    # 如果启动爬虫线程，在程序运行过程中尽量不要修改baseWebs.txt，可以在webs.txt中手工添加监控页面
    # 一旦修改baseWebs.txt，则先[清空webs.txt]再更新webs.txt，重新监控耗时较长
    t3 = threading.Thread(target=crawl.startCrawl, args=(3600,))
    t3.start()
