import requests
import re
import configparser
import math
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def read_conf():
    '''
    读取配置文件
    '''
    cf = configparser.ConfigParser()
    cf.read('51job.conf', encoding='utf8')
    job = str(cf.get('51job', 'job')).split(',')[0]
    city = str(cf.get('51job', 'city')).split(',')
    skill = str(cf.get('51job', 'skill')).split(',')
    return job,city,skill


def get_response(url):
    '''
    请求获得响应，请求超过 3 次失败，返回 None
    '''
    for count in range(3):
        headers = {'User-Agent' : UserAgent().random}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response
    else:
        return


def get_city_code():
    '''
    获得每个城市的编号
    '''
    url = 'https://js.51jobcdn.com/in/js/2016/layer/area_array_c.js?20200305'
    response = get_response(url)
    city_code = response.text.replace('\r\n','')
    city_code = eval(re.findall('var area=(.*?);',city_code)[0])
    city_code = {v : k for k,v in city_code.items()}
    return city_code


def creat_txt():
    '''
    创建 txt 文件
    '''
    f = open('urls.txt','w+')
    f.close()


def get_page(html):
    '''
    计算总页数
    '''
    jobNum = html.find('div',class_='rt').getText()
    jobNum = re.findall('\d+\.?\d*',jobNum)
    if jobNum:
        page = math.ceil(int(jobNum[0])/50)
        return page
    else:
        return 0


def get_job_url(city,job,page):
    '''
    根据总页数提取每一页职位的详细链接
    '''
    print('稍等片刻~~~')
    urls = []
    url = 'https://search.51job.com/list/{},000000,0000,00,9,99,{},2,{}.html'
    for p in range(1,int(page)+1):
        url = url.format(city,job,p)
        response = get_response(url)
        html = BeautifulSoup(response.content.decode('gbk'), 'lxml')
        links = html.find_all('p',class_='t1')
        for link in links:
            link = link.find('a')['href']
            urls.append(link)
    return urls


def get_job_skill(urls,skill):
    '''
    根据岗位详情链接提取任职要求，对技能进行匹配
    若任职要求中有对应的技能，则把 url 保存到 txt
    '''
    print('正在匹配岗位链接。。。')
    for url in urls:
        response = get_response(url)
        html = BeautifulSoup(response.content.decode('gbk'), 'lxml')
        job_req = html.find('div',class_='bmsg job_msg inbox').getText()
        for s in skill:
            if s in job_req:
                write_txt(url)
                break


def write_txt(url):
    '''
    存入 txt
    '''
    with open('urls.txt','a+') as f:
        f.write(url + '\n')


if __name__ == '__main__':
    # 读取配置文件，获得城市编号，创建 txt
    job, city, skill = read_conf()
    city_code = get_city_code()
    creat_txt()

    # 根据城市遍历爬取
    for c in city:
        c = city_code.get(c)
        url = 'https://search.51job.com/list/{},000000,0000,00,9,99,{},2,1.html'
        url = url.format(str(c),str(job))
        response = get_response(url)

        # 判断是否请求失败
        if response == None:
            print('可能网络不太好，请稍后重新运行~')
            break

        # 计算总页数
        html = BeautifulSoup(response.content.decode('gbk'), 'lxml')
        page = get_page(html)
        if page == 0:
            print('在{}没有相关职位'.format(c))
            break

        # 遍历每一页，提取岗位详情链接
        job_url = get_job_url(str(c),str(job),str(page))

        # 提取任职要求
        get_job_skill(job_url,skill)
