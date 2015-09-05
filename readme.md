此程序用于监控WEB网站是否被篡改


进入程序目录，执行命令启动程序：
python main.py

运行时启动三个线程
爬虫线程：监控baseWebs.txt是否发生改变，若发生变化则先【清空webs.txt】再更新webs.txt
过滤线程：监控webs.txt是否发生改变，若发生变化则更新bad.txt和good.txt
监控线程：根据good.txt拨测页面，如果页面md5值发生变化则最多发送3次告警邮件

注意
由于爬虫获取网站所有页面的超链接耗时较长，在不需要的情况下尽量不要启动爬虫线程，可以在webs.txt中手工添加监控页面

同一目录下的文件
CrawlLinks.py：单线程爬虫程序，适用于CPU为主要瓶颈的情况下
MulCrawlLinks.py：多线程爬虫程序，适用于网络延时较大的情况下
WebMonitor.py：监控和过滤程序
baseWebs.txt：WEB网站列表
webs.txt：抓取到的url列表
good.txt：被监控的网站
bad.txt：被剔除的网站，可能是动态页面，也可能是无法访问
log.txt：程序运行日志
