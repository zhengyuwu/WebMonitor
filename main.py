# coding=utf-8
__author__ = "zheng"

import CrawlLinks, MulCrawlLinks
from WebMonitor import webMonitor
import threading

if __name__ == '__main__':
    # 创建一个实例，参数为邮箱及密码
    mon = webMonitor('xxxxxx@189.cn', 'password')

    # 单线程爬虫和多线程爬虫，二选一
    # 单线程爬虫，适用于CPU为主要瓶颈的情况下
    crawl = CrawlLinks.crawlLinks()
    # 多线程爬虫，适用于网络延时较大的情况下
    # crawl = MulCrawlLinks.crawlLinks

    # 过滤线程，参数依次为页面md5值计算间隔（秒），线程挂起时间（秒）
    t1 = threading.Thread(target=mon.startFilter, args=(300, 60))
    # 监控线程，参数依次为页面扫描间隔（秒），连续检测次数
    t2 = threading.Thread(target=mon.startMon, args=(300, 3))
    # 爬虫线程，参数为线程挂起时间（秒）
    # 如果不需要重新爬取baseWebs.txt中的网站所有页面的超链接，则不要启动该线程
    # 如果启动爬虫线程，在程序运行过程中尽量不要修改baseWebs.txt，可以在webs.txt中手工添加监控页面
    # 一旦修改baseWebs.txt，则先[清空webs.txt]再更新webs.txt，重新监控耗时较长
    t3 = threading.Thread(target=crawl.startCrawl, args=(3600,))
    t1.start()
    t2.start()
    t3.start()
