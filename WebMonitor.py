# coding=utf-8
__author__ = "zheng"

import urllib2
import threading
import hashlib
import smtplib
import time


class webMonitor:
    def __init__(self, email, password):

        # 邮箱账号和密码
        self.email = email
        self.password = password
        # 记录邮件发送情况，每个网站最多发送3次邮件
        self.sendEmailTimes = {}

        # 程序是否初始运行，[过滤线程filter是否第一次运行,监控线程startMon是否第一次运行]
        self.firstRun = [True, True]

        # good.txt和webs.txt文件锁
        self.lock_file = threading.Lock()

        # webs.txt文件是否发生变更
        self.webListChange = False
        # webs.txt文件的md5值
        self.fileWebsMd5 = ''

        # web过滤线程
        # 存储所有web链接及相关信息，存储结构：{'网站url':['邮箱','其它信息'],...}
        # self.webs={}

        # 存储web页面过滤时的访问状态及md5值或错误信息，存储结构：{'网站url':[(访问状态,'md5值或错误信息'),...],...}
        self.webMsg = {}

        # web监控线程
        # 监控列表，存储监控页面的正确md5值，保存在文件good.txt中，存储结构：{'网站url':'md5值',...}
        # self.webMd5={}

        # 存储web页面监控时的访问状态及md5值或错误信息，存储结构：{'网站url':[(访问状态,'md5值或错误信息'),...],...}
        self.webMon = {}

    def calFileMd5(self, fileName):
        try:
            with open(fileName, 'r') as f:
                fileMd5 = hashlib.md5(f.read()).hexdigest()
        except Exception, e:
            print u'文件%s操作失败' % fileName
            return 1
        return fileMd5

    # 读取webs.txt文件
    def getWebs(self):
        webs = {}
        try:
            with open('webs.txt', 'r') as f:
                for line in f:
                    line = line.decode('gbk', 'ignore').strip('\r\n\t ')
                    if not line: continue
                    if line.startswith('#'):
                        continue
                    item = line.split('\t', 2)
                    if len(item) == 2:
                        item[2] = ''
                    if len(item) == 1:
                        print u'\r\n网站信息录入错误（webs.txt）：%s' % line
                        continue
                    webs[item[0]] = [item[1], item[2]]
        except Exception, e:
            print u'Error: 文件webs.txt操作失败'
            print e
            return 1
        return webs

    # 读取good.txt文件
    def getWebMd5(self):
        webMd5 = {}
        try:
            with open('good.txt', 'r') as f:
                for line in f:
                    line = line.decode('gbk', 'ignore').strip('\r\n\t ')
                    if line.startswith('#'):
                        continue
                    item = line.split('\t', 2)
                    webMd5[item[0]] = item[1]
        except Exception, e:
            print u'Error: 文件good.txt操作失败'
            print e
            return 1
        return webMd5

    # 单线程计算web页面的md5值，并执行结果存储在store中
    def websHash(self, urls, store={}):
        status = 0
        info = ''
        for url in urls:
            request = urllib2.Request(url)
            try:
                response = urllib2.urlopen(request, timeout=5)
            except urllib2.HTTPError, e:
                status = 1
                info = str(e.code) + '(' + str(e.msg) + ')'
            except urllib2.URLError, e:
                status = 2
                info = str(e.reason)
            except Exception, e:
                status = 3
                info = str(e.args)
            else:
                status = 0
                content = response.read()
                response.close()
                info = hashlib.md5(content).hexdigest()
            if store.has_key(url):
                store[url].append((status, info))
            else:
                store[url] = [(status, info)]
            print 'Access: ', url, status, info
        return (status, info)

    # 多线程执行网站页面的md5计算，并将计算结果保存在store中
    def mulCalMd5(self, urls, store={}):
        # 分组url，由不同的线程执行md5计算，存储结构：{线程No:[url,'http://202.105.213.21',...]}
        urlSplit = {}

        # 线程编号
        No = 0
        urlSplit[No] = []

        # 每线程负责20个页面的md5计算
        count = 0

        for url in urls:
            count += 1
            urlSplit[No].append(url)
            # 每线程负责60个页面的md5计算
            if count > 60:
                No += 1
                urlSplit[No] = []
                count = 0
        # print urlSplit

        # 启动线程执行web页面md5计算，计算结果存储在store中
        threads = {}
        for key in urlSplit:
            threads[key] = threading.Thread(target=self.websHash, args=(urlSplit[key], store))
            threads[key].start()
            # print '启动线程：threads[%s]' % key
        for key in urlSplit:
            threads[key].join(60)

    # 过滤进程
    # 过滤动态页面或访问异常的页面，每个页面计算3次md5值，计算间隔为period秒，对3次计算结果进行对比
    # 如果网站列表未发生改变，过滤进程则挂起sleep秒
    def startFilter(self, period=60, sleep=60):
        print u'====过滤线程开始运行......'
        while True:
            fileWebsMd5 = self.calFileMd5('webs.txt')
            if self.firstRun[0]:
                self.webListChange = True
                self.fileWebsMd5 = fileWebsMd5
            elif self.fileWebsMd5 == fileWebsMd5:
                print u'过滤线程：网站列表未发生改变，不需要执行网站信息更新'
                print u'过滤线程：挂起%s秒' % sleep
                time.sleep(sleep)
                continue
            else:
                print u'====过滤线程：网站列表发生改变，需要执行网站信息更新'
                self.fileWebsMd5 = fileWebsMd5
                self.webListChange = True

            # 获取文件锁
            print u'过滤线程：等待获取文件锁'
            self.lock_file.acquire()
            print u'过滤线程：成功获取文件锁'
            print u'过滤线程：执行网站信息更新，请稍等'

            print u'过滤线程：从文件webs.txt中读取网站列表'
            # 对self.webs加锁
            # self.lock_webs.acquire()

            webs = self.getWebs()

            # 释放self.webs的锁
            # self.lock_webs.release()
            print u'过滤线程：网站列表读取完成'

            print u'过滤线程：过滤动态页面或访问异常的页面'
            print ''
            self.webMsg.clear()
            print u'过滤线程：执行第一次md5采集'
            self.mulCalMd5(webs, self.webMsg)
            print u'过滤线程：等待%s秒再执行第二次md5采集' % period
            time.sleep(period)
            self.mulCalMd5(webs, self.webMsg)
            print u'过滤线程：等待%s秒再执行第三次md5采集' % period
            time.sleep(period)
            self.mulCalMd5(webs, self.webMsg)

            # 存储可监控网站的url和md5值
            webMd5 = {}
            print ''
            for url in self.webMsg:
                # 获取页面访问成功情况下的md5值的列表
                md5List = []
                for item in self.webMsg[url]:
                    if item[0] == 0:
                        md5List.append(item[1])

                lenth = len(md5List)
                if lenth == 2 and md5List[0] == md5List[1]:
                    webMd5[url] = md5List[0]
                    print 'Add: ' + url + '\t' + webs[url][1] + '\t' + str(self.webMsg[url])
                    continue
                if lenth == 3 and md5List[0] == md5List[1] and md5List[0] == md5List[2]:
                    webMd5[url] = md5List[0]
                    print 'Add: ' + url + '\t' + webs[url][1] + '\t' + str(self.webMsg[url])
                    continue
                try:
                    with open('bad.txt', 'a') as f:
                        text = 'Remove: ' + url + '\t' + webs[url][0] + '\t' + webs[url][1] + '\t' + str(
                            self.webMsg[url])
                        print text
                        f.write(text.encode('gbk', 'ignore') + '\r\n')
                except Exception, e:
                    print u'Error: 文件bad.txt操作失败'
                    print e
            # print webMd5
            try:
                with open('good.txt', 'w') as f:
                    for url in webMd5:
                        f.write(url + '\t' + webMd5[url] + '\r\n')
            except Exception, e:
                print u'Error: 文件good.txt操作失败'
                print e

            print u'过滤线程：网站信息更新完成'
            print u'过滤线程：释放文件锁'
            self.lock_file.release()
            self.firstRun[0] = False
        print u'====过滤线程停止运行......'

    # 监控进程
    # period: 扫描间隔，单位秒；times: 连续检测次数
    def startMon(self, period=300, times=3):
        print u'====监控线程开始运行......'
        webs = {}
        webMd5 = {}
        while True:
            if self.firstRun[0]:
                time.sleep(10)
                continue
            if self.webListChange or self.firstRun[1]:
                print u'====监控线程：网站列表发生改变，需要重新获取网站数据'
                print u'监控线程：等待获取文件锁'
                self.lock_file.acquire()
                print u'监控线程：成功获取文件锁'
                webs = self.getWebs()
                webMd5 = self.getWebMd5()
                print u'监控线程：网站数据获取完成'
                print u'监控线程，释放文件锁'
                self.lock_file.release()
                self.webListChange = False
                self.firstRun[1] = False

            # self.webMon={'url':[(status1,'hash1'),(status2,'hash2'),(status3,'hash3'),...],...}
            self.webMon.clear()
            for i in range(times):
                print u'监控线程：执行网站扫描'
                self.mulCalMd5(webMd5, self.webMon)
                print u'监控线程：挂起%s秒' % period
                time.sleep(period)
            for url in self.webMon:
                right = False
                for i in range(times):
                    if self.webMon[url][i][0] == 0 and self.webMon[url][i][1] == webMd5[url]:
                        right = True
                        break
                if not right:
                    message = time.strftime('%Y-%m-%d %H:%M:%S') + ', ' + url + ', ' + webs[url][
                        1] + ': ' + 'maybe change.'
                    # print message
                    try:
                        with open('log.txt', 'a') as f:
                            alert = 'Alert: ' + message + '\r\n'
                            f.write(alert.encode('gbk', 'ignore'))
                    except Exception, e:
                        print u'操作文件log.txt失败，程序忽略该问题，继续执行'
                        print e
                    print 'Alert: ' + message
                    if self.sendEmailTimes.has_key(url):
                        if self.sendEmailTimes[url] >= 3:
                            continue
                        elif self.sendEmail(webs[url][0], message) == 0:
                            self.sendEmailTimes[url] += 1
                    elif self.sendEmail(webs[url][0], message) == 0:
                        self.sendEmailTimes[url] = 1
        print u'====监控线程停止运行......'

    # 发送告警邮件
    def sendEmail(self, receiver, text):
        sendTo = receiver
        rec = []
        rec.append(receiver)
        server = smtplib.SMTP()
        text = text.encode('base64')
        msg = 'From:%s\r\nTo:%s\r\nSubject:Web Hash Alert\r\nContent-Type:text/html\r\nContent-Transfer-Encoding:base64\r\n\r\n%s' \
              % (self.email, sendTo, text)
        try:
            server.connect('smtp.189.cn', 25)
            server.login(self.email, self.password)
            server.sendmail(self.email, rec, msg)
        except Exception, e:
            print u'====邮件发送失败：'
            print msg
            print e
            with open('log.txt', 'a') as f:
                f.write('\r\n' + 'Alert: Send email error!' + '\r\n' + msg + '\r\n')
            return 2

        print u'邮件发送成功：'
        print msg

        with open('log.txt', 'a') as f:
            f.write('\r\n' + 'Send email success: ' + '\r\n' + msg + '\r\n')
        return 0


if __name__ == '__main__':
    # 可以运行该程序，只启动过滤线程和监控线程
    # 创建一个实例，参数为邮箱及密码
    mon = webMonitor('xxxxxx@189.cn', 'password')
    # 过滤线程，参数依次为页面md5值计算间隔（秒），线程挂起时间（秒）
    t1 = threading.Thread(target=mon.startFilter, args=(300, 60))
    # 监控线程，参数依次为页面扫描间隔（秒），连续检测次数
    t2 = threading.Thread(target=mon.startMon, args=(300, 3))
    t1.start()
    t2.start()
