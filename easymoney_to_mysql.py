"""
e.g: http://data.eastmoney.com/bbsj/201806/lrb.html
"""
from sqlalchemy import create_engine
import requests
import re
from multiprocessing import Pool
import json
import csv
import pandas as pd
import os
import time
import numpy as np

def get_engine():
    engine = create_engine('mysql://root:111111@127.0.0.1/tushare?charset=utf8')
    return engine

engine = get_engine()

# 1 设置表格爬取时期
#1-业绩报表；2-业绩快报表：3-业绩预告表；4-预约披露时间表；5-资产负债表；6-利润表；7-现金流量表
def set_table(year,quarter,tables):
    print('*' * 80)
    print('\t\t\t\t东方财富网报表下载')
    print('--------------')

    # 1 设置财务报表获取时期
    # year = int(float(input('请输入要查询的年份(四位数2007-2018)：\n')))
    # int表示取整，里面加float是因为输入的是str，直接int会报错，float则不会
    # https://stackoverflow.com/questions/1841565/valueerror-invalid-literal-for-int-with-base-10
    # while (year < 2007 or year > 2018):
        # year = int(float(input('年份数值输入错误，请重新输入：\n')))
    # year = 2010

   # quarter = int(float(input('请输入小写数字季度(1:1季报，2-年中报，3：3季报，4-年报)：\n')))
   # while (quarter < 1 or quarter > 4):
   #     quarter = int(float(input('季度数值输入错误，请重新输入：\n')))
   #
    # quarter = 4
    # 转换为所需的quarter 两种方法,2表示两位数，0表示不满2位用0补充，
    # http://www.runoob.com/python/att-string-format.html
    quarter = '{:02d}'.format(quarter * 3)
    # quarter = '%02d' %(int(month)*3)

    # 确定季度所对应的最后一天是30还是31号
    if (quarter == '06') or (quarter == '09'):
        day = 30
    else:
        day = 31
    date = '{}-{}-{}' .format(year, quarter, day)
    # print('date:', date)  # 测试日期 ok

    # 2 设置财务报表种类
    #tables = int(
    #    input('请输入查询的报表种类对应的数字(1-业绩报表；2-业绩快报表：3-业绩预告表；4-预约披露时间表；5-资产负债表；6-利润表；7-现金流量表): \n'))
    # tables = 5

    dict_tables = {1: '业绩报表', 2: '业绩快报表', 3: '业绩预告表',
                   4: '预约披露时间表', 5: '资产负债表', 6: '利润表', 7: '现金流量表'}

    dict = {1: 'YJBB', 2: 'YJKB', 3: 'YJYG',
            4: 'YYPL', 5: 'ZCFZB', 6: 'LRB', 7: 'XJLLB'}
    category = dict[tables]

    # js请求参数里的type，第1-4个表的前缀是'YJBB20_'，后3个表是'CWBB_'
    # 设置set_table()中的type、st、sr、filter参数
    if tables == 1:
        category_type = 'YJBB20_'
        st = 'latestnoticedate'
        sr = -1
        filter =  "(securitytypecode in ('058001001','058001002'))(reportdate=^%s^)" %(date)
    elif tables == 2:
        category_type = 'YJBB20_'
        st = 'ldate'
        sr = -1
        filter = "(securitytypecode in ('058001001','058001002'))(rdate=^%s^)" %(date)
    elif tables == 3:
        category_type = 'YJBB20_'
        st = 'ndate'
        sr = -1
        filter=" (IsLatest='T')(enddate=^2018-06-30^)"
    elif tables == 4:
        category_type = 'YJBB20_'
        st = 'frdate'
        sr = 1
        filter =  "(securitytypecode ='058001001')(reportdate=^%s^)" %(date)
    else:
        category_type = 'CWBB_'
        st = 'noticedate'
        sr = -1
        filter = '(reportdate=^%s^)' % (date)

    category_type = category_type + category
    # print(category_type)
    # 设置set_table()中的filter参数

    yield{
    'date':date,
    'category':dict_tables[tables],
    'category_type':category_type,
    'st':st,
    'sr':sr,
    'filter':filter
    }

# 2 设置表格爬取起始页数
def page_choose(page_all):

    # 选择爬取页数范围    
    # start_page = int(input('请输入下载起始页数：\n'))
    # nums = input('请输入要下载的页数，（若需下载全部则按回车）：\n')
    # print('*' * 80)

    # 判断输入的是数值还是回车空格
    # if nums.isdigit():
        # end_page = start_page + int(nums)
    # elif nums == '':
        # end_page = int(page_all.group(1))
    # else:
        # print('页数输入错误')

    # 返回所需的起始页数，供后续程序调用
    start_page = 1
    end_page = int(page_all.group(1))
    yield{
        'start_page': start_page,
        'end_page': end_page
    }

# 3 表格正式爬取
def get_table(date, category_type,st,sr,filter,page):
    # 参数设置
    params = {
        # 'type': 'CWBB_LRB',
        'type': category_type,  # 表格类型
        'token': '70f12f2f4f091e459a279469fe49eca5',
        'st': st,
        'sr': sr,
        'p': page,
        'ps': 50,  # 每页显示多少条信息
        'js': 'var LFtlXDqn={pages:(tp),data: (x)}',
        'filter': filter,
        # 'rt': 51294261  可不用
    }
    url = 'http://dcfm.eastmoney.com/em_mutisvcexpandinterface/api/js/get?'

    # print(url)
    response = requests.get(url, params=params).text
    # print(response)
    # 确定页数
    pat = re.compile('var.*?{pages:(\d+),data:.*?')
    page_all = re.search(pat, response)
    print(page_all.group(1))  # ok

    # 提取{},json.loads出错
    # pattern = re.compile('var.*?data: \[(.*)]}', re.S)

    # 提取出list，可以使用json.dumps和json.loads
    pattern = re.compile('var.*?data: (.*)}', re.S)
    items = re.search(pattern, response)
    # 等价于
    # items = re.findall(pattern,response)
    # print(items[0])
    data = items.group(1)
    data = json.loads(data)
    # data = json.dumps(data,ensure_ascii=False)

    return page_all, data,page

# 写入表头
# 方法1 借助csv包，最常用
def write_header(data,category):
    with open('{}.csv' .format(category), 'a', encoding='utf_8_sig', newline='') as f:
        headers = list(data[0].keys())
        # print(headers)  # 测试 ok
        writer = csv.writer(f)
        writer.writerow(headers)

def write_table(data,page,category_type):
    print('\n正在下载第 %s 页表格' % page)
    #print(data)
    if category_type == 'CWBB_ZCFZB':#资产负债表
        table_name = 'easymoney_asset'
    elif category_type == 'CWBB_LRB':#利润表
        table_name = 'easymoney_profit'
    elif category_type == 'CWBB_XJLLB':#现金流量表
        table_name = 'easymoney_cash'
    elif category_type == 'YJBB20_YJBB':#业绩报表
        table_name = 'easymoney_yeji'
    else :
        os._exit(0)

    #engine = get_engine()
    # 写入文件方法1
    all_values = []
    keys = []
    for d in data:
        vals = d.values()
        all_values.append(vals)
        keys = d.keys()

    df = pd.DataFrame(all_values,columns=keys)
    df = df.set_index('scode')
    df.to_sql(table_name,engine,if_exists='append')#存入数据库,同花顺pe数据


#主方法
def main(date, category_type,st,sr,filter,page):
    func = get_table(date, category_type,st,sr,filter,page)
    data = func[1]
    page = func[2]
    write_table(data,page,category_type)


#资产负债表 to mysql
def asset(year,quarter):
    main_data_to_db(year,quarter,5)

#利润表 to mysql
def profit(year,quarter):
    main_data_to_db(year,quarter,6)

#现金流量表 to mysql
def cash(year,quarter):
    main_data_to_db(year,quarter,7)
    
#业绩报表 to mysql
def yeji(year,quarter):
    main_data_to_db(year,quarter,1)

#获取数据并存储到mysql，主方法
#tables : 1-业绩报表；2-业绩快报表：3-业绩预告表；4-预约披露时间表；5-资产负债表；6-利润表；7-现金流量表
def main_data_to_db(year,quarter,tables):
    # 获取总页数，确定起始爬取页数
    for i in set_table(year,quarter,tables):
        date = i.get('date')
        category = i.get('category')
        category_type = i.get('category_type')
        st = i.get('st')
        sr = i.get('sr')
        filter = i.get('filter')

    constant = get_table(date,category_type,st,sr,filter, 1)
    page_all = constant[0]

    for i in page_choose(page_all):
        start_page = i.get('start_page')
        end_page = i.get('end_page')

    start_time = time.time()  # 下载开始时间
    # 爬取表格主程序
    for page in range(start_page, end_page):
        main(date,category_type,st,sr,filter, page)
    
    end_time = time.time() - start_time  # 结束时间
    print('下载完成')
    print('下载用时: {:.1f} s' .format(end_time))


#初始数据
def data_init():
    for year in range(2006,2020):
        for jidu in range(1,5):
            print(year,jidu)
            # asset(year,jidu)
            # profit(year,jidu)
            # cash(year,jidu)
            yeji(year,jidu)

data_init()
