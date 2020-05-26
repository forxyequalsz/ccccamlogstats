import os
import re
import datetime
import xlsxwriter

# 初始化总数计数器
case_count = 0
error_count = 0
# 初始化ETC交易计数器
etc_count = 0
etc_aamount_count = 0
etc_damount_count = 0
etc_tamount_count = 0
# 初始化CPC交易计数器
cpc_count = 0
cpc_aamount_count = 0
cpc_damount_count = 0
cpc_tamount_count = 0
# ETC运行计数器
etc_suc_count = 0
etc_fail_count = 0
etc_except_count_u = 0
etc_except_count_d = 0
# CPC运行计数器
cpc_suc_count = 0
cpc_fail_count = 0
cpc_except_count_u = 0
cpc_except_count_d = 0
# 车型计数器
# 无标识与一到四型客车
car_count = [0, 0, 0, 0, 0]
car_aa_count = [0, 0, 0, 0, 0]
car_da_count = [0, 0, 0, 0, 0]
car_ta_count = [0, 0, 0, 0, 0]
# 一到六型货车和未知的17型车辆
truck_count = [0, 0, 0, 0, 0, 0, 0]
truck_aa_count = [0, 0, 0, 0, 0, 0, 0]
truck_da_count = [0, 0, 0, 0, 0, 0, 0]
truck_ta_count = [0, 0, 0, 0, 0, 0, 0]
# 特殊车辆
spec_vech_count = [0, 0, 0, 0, 0, 0]
spec_vech_aa_count = [0, 0, 0, 0, 0, 0]
spec_vech_da_count = [0, 0, 0, 0, 0, 0]
spec_vech_ta_count = [0, 0, 0, 0, 0, 0]
# 初始化buffer
buffer_0 = []
buffer_1 = []
merge_count = 0
# 初始化存储类型变量
# 0为etc成功，1为etc失败，2为cpc成功，3为cpc失败
save_flag = False
save_type = 0
# 初始化输入检查器，True为继续检查，False为检查通过
input_check = True


# 提取流水编号和PASSID
# ETC和CPC的字段结构较为统一
def extract_keyword_1(line):
    pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
              '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<mac_address>[^\[\]]{8,})\])(?:\[(?P<serial_number>[^\[\]]{35,})\])' \
              '[^s]*PASSID:(?P<pass_id>[\w]{36,}),*'
    regex = re.compile(pattern)
    matcher = regex.match(line)
    if matcher:
        return matcher.groupdict()
    else:
        # 查错用语句
        print(line)
        print(matcher)
        return matcher


# 对ETC特情进行排除
def not_count_etc(case):
    global etc_except_count_u
    global etc_except_count_d
    pattern_u = '145|146|147|148|149|150|151|152|153|154|155|156|157|158|159|160|161|162|163|164|165|166|167|168|169|170|' \
              '171|172|173|174|175|176|177|178|179|180|181|182|183|184|186|189|191|192|193|199'
    pattern_d = '154|186|189|193'
    regex_u = re.compile(pattern_u)
    matcher_u = regex_u.findall(case)
    regex_d = re.compile(pattern_d)
    matcher_d = regex_d.findall(case)
    if matcher_u:
        etc_except_count_u += 1
    if matcher_d:
        etc_except_count_d += 1
    return


# 提取ETC字段
# ETC特情提取
def etc_fail_unpack(line):
    global save_type
    global error_count
    # 变量名规则：
    # antenna_no-天线编号；ip_address-ip地址（我也不知道是不是）；case_type-交易类型；mac_address-MAC地址；plate_spec-车牌号；
    # vech_type-车辆类型；label_suc-标签交易成功位；obu_suc-复合交易成功位；able_amount-应收金额；disc_amount-优惠金额；
    # trans_amount-交易金额；fact_amount-实际扣款；event_spec-特情编号
    pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
              '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<sw_version>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
              'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]+)\s车型:(?P<vech_type>[^s]+)\s' \
              '(?P<label_suc>[^s]+)\s(?P<obu_suc>[^s]+)\s应收金额:(?P<able_amount>[\d]+)\s' \
              '优惠金额:(?P<disc_amount>[\d\-]+)\s交易金额:(?P<trans_amount>[\d]+)\s实际扣款:(?P<fact_amount>[\d]+)\s' \
              '交易特情:(?P<event_spec>[\d|]+)\s*'
    regex = re.compile(pattern)
    matcher = regex.match(line)
    # 特殊特情
    if matcher is None:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<sw_version>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]*)\s车型:(?P<vech_type>[^s]+)\s' \
                  '(?P<label_suc>[^s]+)(?P<obu_suc>[^s]*)(?P<able_amount>[\d]*)' \
                  '(?P<disc_amount>[\d]*)(?P<trans_amount>[\d]*)(?P<fact_amount>[\d]*)' \
                  '\s交易特情:(?P<event_spec>[\d|]+)\s*'
        regex = re.compile(pattern)
        matcher = regex.match(line)
    # 特别特殊特情：无特情号（目前仅遇到2例）
    if matcher is None:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<ip_address>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]*)\s车型:(?P<vech_type>[\d]+)\s' \
                  '(?P<label_suc>[^s]+)\s(?P<obu_suc>[^s]+)\s应收金额:(?P<able_amount>[\d]*)\s' \
                  '优惠金额:(?P<disc_amount>[\d]*)\s交易金额:(?P<trans_amount>[\d]*)\s实际扣款:(?P<fact_amount>[\d]*)\s' \
                  '(?P<event_spec>[\d|]*)\s*'
        regex = re.compile(pattern)
        matcher = regex.match(line)
    # 特别特别特殊特情：ETC交易无标签，无特情号（无语……）
    if matcher is None:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<ip_address>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]*)\s车型:(?P<vech_type>[\d]+)\s' \
                  '(?P<label_suc>[^s]{,4})\s(?P<able_amount>[^\[]*)' \
                  '(?P<disc_amount>[^\[]*)(?P<trans_amount>[^\[]*)(?P<fact_amount>[^\[]*)' \
                  '(?P<event_spec>[^\[]*)*'
        regex = re.compile(pattern)
        matcher = regex.match(line)
    save_type = 1
    # 无法匹配的特情处理
    if matcher is None:
        error_count += 1
        print('[ERROR]出现特例语句，请根据时间戳手动搜索处理：\n' + line)
        return
    return matcher.groupdict()


# 提取ETC字段
def extract_keyword_etc(line):
    global save_type
    # ETC交易计数器
    global etc_count
    global etc_aamount_count
    global etc_damount_count
    global etc_tamount_count
    global etc_suc_count
    global etc_fail_count

    # 失败的交易有单失败（复合失败）和全失败
    suc_check = '交易失败'
    suc_check_result = re.search(suc_check, line)
    # 判定成功为监测到“交易失败”
    if suc_check_result:
        # 去找失败分析方法
        matcher = etc_fail_unpack(line)
        etc_fail_count += 1
        not_count_etc(matcher['event_spec'])
    else:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<sw_version>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]+)\s车型:(?P<vech_type>[\d]+)\s' \
                  '(?P<label_suc>[^s]+)\s(?P<obu_suc>[^s]+)\s应收金额:(?P<able_amount>[\d]+)\s' \
                  '优惠金额:(?P<disc_amount>[\d\-]+)\s交易金额:(?P<trans_amount>[\d]+)\s实际扣款:(?P<fact_amount>[\d]+)*'
        regex = re.compile(pattern)
        match = regex.match(line)
        if match is not None:
            matcher = match.groupdict()
        else:
            return match
        etc_suc_count += 1  # 计入etc成功数
        save_type = 0  # 保存为etc成功型
        # 取数
        if matcher['able_amount'] != '' and matcher['disc_amount'] != '' and matcher['trans_amount'] != '':
            able_amount = int(matcher['able_amount'])
            disc_amount = int(matcher['disc_amount'])
            trans_amount = int(matcher['trans_amount'])
        else:
            able_amount = 0
            disc_amount = 0
            trans_amount = 0
        # 计算应收金额
        etc_aamount_count = etc_aamount_count + able_amount
        # 计算优惠金额
        etc_damount_count = etc_damount_count + disc_amount
        # 计算交易金额
        etc_tamount_count = etc_tamount_count + trans_amount
    return matcher


# 对CPC特情进行排除
def not_count_cpc(case):
    global cpc_except_count_u
    global cpc_except_count_d
    pattern_u = '145|146|147|148|149|150|151|152|153|154|155|156|157|158|159|160|161|162|163|164|165|166|167|168|169|170|' \
              '171|172|173|174|175|176|177|178|179|180|181|182|183|184|186|189|191|192|193|199'
    pattern_d = '154|186|189|193'
    regex_u = re.compile(pattern_u)
    matcher_u = regex_u.findall(case)
    regex_d = re.compile(pattern_d)
    matcher_d = regex_d.findall(case)
    if matcher_u:
        cpc_except_count_u += 1
    if matcher_d:
        cpc_except_count_d += 1
    return


# CPC特情提取
def cpc_fail_unpack(line):
    global save_type
    global error_count
    pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
              '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<sw_version>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
              'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]+)\s车型:(?P<vech_type>[^s]+)\s' \
              '(?P<trans_suc>[^s]+)\s应收金额:(?P<able_amount>[\d]+)\s' \
              '优惠金额:(?P<disc_amount>[\d\-]+)\s交易金额:(?P<trans_amount>[\d]+)\s实际扣款:(?P<fact_amount>[\d]+)\s' \
              '交易特情:(?P<event_spec>[\d|]+)\s*'
    regex = re.compile(pattern)
    matcher = regex.match(line)
    # 特殊特情
    if matcher is None:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<sw_version>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]*)\s车型:(?P<vech_type>[^s]+)\s' \
                  '(?P<trans_suc>[^s]+)\s(?P<able_amount>[\d]*)' \
                  '(?P<disc_amount>[\d]*)(?P<trans_amount>[\d]*)(?P<fact_amount>[\d]*)' \
                  '交易特情:(?P<event_spec>[\d|]+)\s*'
        regex = re.compile(pattern)
        matcher = regex.match(line)
    # 特别特殊特情：无特情号（目前云南发现）
    if matcher is None:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<ip_address>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]*)\s车型:(?P<vech_type>[\d]+)\s' \
                  '(?P<trans_suc>[^s]{,4})\s(?P<able_amount>[^\[]*)' \
                  '(?P<disc_amount>[^\[]*)(?P<trans_amount>[^\[]*)(?P<fact_amount>[^\[]*)' \
                  '(?P<event_spec>[^\[]*)*'
        regex = re.compile(pattern)
        matcher = regex.match(line)
    save_type = 3
    # 无法匹配的特情处理
    if matcher is None:
        error_count += 1
        print('[ERROR]出现特例语句，请根据时间戳手动搜索处理：\n' + line)
        return
    return matcher.groupdict()


# 提取CPC字段
def extract_keyword_cpc(line):
    global save_type
    # CPC交易计数器
    global cpc_aamount_count
    global cpc_damount_count
    global cpc_tamount_count
    global cpc_suc_count
    global cpc_fail_count

    suc_check = '交易失败'
    suc_check_result = re.search(suc_check, line)
    # 判定成功为监测到“交易失败”
    if suc_check_result:
        # 去找失败分析方法
        matcher = cpc_fail_unpack(line)
        cpc_fail_count += 1
        not_count_cpc(matcher['event_spec'])
    else:
        pattern = '(?P<time_stamp>[\d\:\.]+)\s(?:\[(?P<case_type>[^\[\]]+)\])\s(?:\[(?P<number>[^\[\]]+)\])\s' \
                  '(?:\[(?P<antenna_no>[^\[\]]+)\])(?:\[(?P<sw_version>[^\[\]]+)\])\*(?P<trade_type>[\S]+)\s' \
                  'MAC:(?P<mac_address>[^s]+)\s车牌号:(?P<plate_spec>[^s]+)\s车型:(?P<vech_type>[\d]+)\s' \
                  '(?P<trans_suc>[^s]+)\s应收金额:(?P<able_amount>[\d]+)\s优惠金额:(?P<disc_amount>[\d\-]+)\s' \
                  '交易金额:(?P<trans_amount>[\d]+)\s实际扣款:(?P<fact_amount>[\d]+)*'
        regex = re.compile(pattern)
        match = regex.match(line)
        if match is not None:
            matcher = match.groupdict()
        else:
            return match
        cpc_suc_count += 1      # 计入cpc成功数
        save_type = 2           # 保存为cpc成功型
        # 取数
        if matcher['able_amount'] != '' and matcher['disc_amount'] != '' and matcher['trans_amount'] != '':
            able_amount = int(matcher['able_amount'])
            disc_amount = int(matcher['disc_amount'])
            trans_amount = int(matcher['trans_amount'])
        else:
            able_amount = 0
            disc_amount = 0
            trans_amount = 0
        # 计算应收金额
        cpc_aamount_count = cpc_aamount_count + able_amount
        # 计算优惠金额
        cpc_damount_count = cpc_damount_count + disc_amount
        # 计算交易金额
        cpc_tamount_count = cpc_tamount_count + trans_amount
    return matcher


# 提取交易信息
# ETC和CPC交易结构不同
def extract_keyword_2(line):
    # 初始化计数器
    global error_count
    global etc_count
    global cpc_count

    pattern = 'ETC|CPC'
    searcher = re.search(pattern, line)
    # 分类型处理
    # 若监测到关键词，按词处理
    if searcher:
        # 类型检查，返回字段
        if searcher.group() == 'ETC':
            etc_count += 1
            matcher = extract_keyword_etc(line)
        elif searcher.group() == 'CPC':
            cpc_count += 1
            matcher = extract_keyword_cpc(line)
    if matcher is None:
        print('出现特例:' + line)
        error_count += 1
        return
    return matcher


# 车型统计
def car_type_count(buffer):
    # 声明全局变量
    # 无标识与一到四型客车
    global car_count
    global car_aa_count
    global car_da_count
    global car_ta_count
    # 一到六型货车和未知的17型车辆
    global truck_count
    global truck_aa_count
    global truck_da_count
    global truck_ta_count
    # 特殊车辆
    global spec_vech_count
    global spec_vech_aa_count
    global spec_vech_da_count
    global spec_vech_ta_count

    vech_type = int(buffer['vech_type'])
    if buffer['able_amount'] != '' and buffer['disc_amount'] != '' and buffer['trans_amount'] != '':
        able_amount = int(buffer['able_amount'])
        disc_amount = int(buffer['disc_amount'])
        trans_amount = int(buffer['trans_amount'])
    else:
        able_amount = 0
        disc_amount = 0
        trans_amount = 0
    if vech_type < 5:
        car_count[vech_type] += 1
        car_aa_count[vech_type] = car_aa_count[vech_type] + able_amount
        car_da_count[vech_type] = car_da_count[vech_type] + disc_amount
        car_ta_count[vech_type] = car_ta_count[vech_type] + trans_amount
    elif vech_type > 10 and vech_type < 17:
        vech_type = vech_type - 11
        truck_count[vech_type] += 1
        truck_aa_count[vech_type] = truck_aa_count[vech_type] + able_amount
        truck_da_count[vech_type] = truck_da_count[vech_type] + disc_amount
        truck_ta_count[vech_type] = truck_ta_count[vech_type] + trans_amount
    elif vech_type > 20 and vech_type < 27:
        vech_type = vech_type - 21
        spec_vech_count[vech_type] += 1
        spec_vech_aa_count[vech_type] = spec_vech_aa_count[vech_type] + able_amount
        spec_vech_da_count[vech_type] = spec_vech_da_count[vech_type] + disc_amount
        spec_vech_ta_count[vech_type] = spec_vech_ta_count[vech_type] + trans_amount
    else:
        truck_count[6] += 1
        truck_aa_count[6] = truck_aa_count[6] + able_amount
        truck_da_count[6] = truck_da_count[6] + disc_amount
        truck_ta_count[6] = truck_ta_count[6] + trans_amount
    return


# 保存统计结果
def save_stats_result():
    # 先写表头
    title_column = ['一型客车', '二型客车', '三型客车', '四型客车', '一型货车', '二型货车', '三型货车', '四型货车','五型货车',
                   '六型货车', '一型专项作业车', '二型专项作业车', '三型专项作业车', '四型专项作业车', '五型专项作业车',
                   '六型专项作业车', '无法识别车型', '特殊识别编号']
    title_row = ['数量', '应收金额（元）', '折扣金额（元）', '交易金额（元）']
    worksheet_0.write_column('A2', title_column)
    worksheet_0.write_row('B1', title_row)
    # 建立数据列表
    count_list = car_count[1:] + truck_count[:-1] + spec_vech_count[:] + [car_count[0], truck_count[-1]]
    aa_list = car_aa_count[1:] + truck_aa_count[:-1] + spec_vech_aa_count[:] + [car_aa_count[0], truck_aa_count[-1]]
    da_list = car_da_count[1:] + truck_da_count[:-1] + spec_vech_da_count[:] + [car_da_count[0], truck_da_count[-1]]
    ta_list = car_ta_count[1:] + truck_ta_count[:-1] + spec_vech_ta_count[:] + [car_ta_count[0], truck_ta_count[-1]]
    # 除100
    for i in range(0, len(count_list)):
        aa_list[i] = aa_list[i] / 100
        da_list[i] = da_list[i] / 100
        ta_list[i] = ta_list[i] / 100
    # 设置列宽
    worksheet_0.set_column('A:E', 20)
    # 写入统计结果
    worksheet_0.write_column('B2', count_list)
    worksheet_0.write_column('C2', aa_list)
    worksheet_0.write_column('D2', da_list)
    worksheet_0.write_column('E2', ta_list)
    return


# 初次筛选，确认是流水数据行还是交易信息行
def check_keywords(line):
    # 声明计数器
    global buffer_0
    global buffer_1
    global case_count
    global merge_count
    global error_count

    pattern = '流水数据|车牌号:'
    searcher = re.search(pattern, line)
    # 分类型处理
    # 若监测到关键词，按词处理
    if searcher:
        # 类型检查，返回给缓冲区
        if searcher.group() == '流水数据':
            buffer_0 = extract_keyword_1(line)
        elif searcher.group() == '车牌号:':
            case_count += 1
            buffer_1 = extract_keyword_2(line)
            # 车型统计
            if buffer_1 is not None:
                car_type_count(buffer_1)
        if buffer_0 is not None and buffer_1 is not None:
            if len(buffer_0) > 0 and len(buffer_1) > 0:
                if buffer_0['mac_address'] == buffer_1['mac_address']:
                    buffer_0.update(buffer_1)
                    # 长判断，根据save_type，把buffer_0的内容写入xlsx
                    if save_flag is True and save_type == 0:
                        save_title = ['时间戳', '日志类型', '日志号', '天线编号', 'MAC地址', '流水号', 'PASSID',
                                      '软件版本', '交易类型', '车牌号', '车型', '标签交易状态',
                                      '复合交易状态', '应收金额', '优惠金额', '交易金额', '实际扣款']
                        save_list = list(buffer_0.values())
                        for col_num, data in enumerate(save_list):
                            worksheet_1.write(0, col_num, save_title[col_num])
                            worksheet_1.write(etc_suc_count, col_num, data)
                    elif save_flag is True and save_type == 1:
                        save_title = ['时间戳', '日志类型', '日志号', '天线编号', 'MAC地址', '流水号', 'PASSID',
                                      '软件版本', '交易类型', '车牌号', '车型', '标签交易状态',
                                      '复合交易状态', '应收金额', '优惠金额', '交易金额', '实际扣款', '交易特情']
                        save_list = list(buffer_0.values())
                        for col_num, data in enumerate(save_list):
                            worksheet_2.write(0, col_num, save_title[col_num])
                            worksheet_2.write(etc_fail_count, col_num, data)
                    elif save_flag is True and save_type == 2:
                        save_title = ['时间戳', '日志类型', '日志号', '天线编号', 'MAC地址', '流水号', 'PASSID',
                                      '软件版本', '交易类型', '车牌号', '车型', '交易状态',
                                      '应收金额', '优惠金额', '交易金额', '实际扣款']
                        save_list = list(buffer_0.values())
                        for col_num, data in enumerate(save_list):
                            worksheet_3.write(0, col_num, save_title[col_num])
                            worksheet_3.write(cpc_suc_count, col_num, data)
                    elif save_flag is True and save_type == 3:
                        save_title = ['时间戳', '日志类型', '日志号', '天线编号', 'MAC地址', '流水号', 'PASSID',
                                      '软件版本', '交易类型', '车牌号', '车型', '交易状态',
                                      '应收金额', '优惠金额', '交易金额', '实际扣款', '交易特情']
                        save_list = list(buffer_0.values())
                        for col_num, data in enumerate(save_list):
                            worksheet_4.write(0, col_num, save_title[col_num])
                            worksheet_4.write(cpc_fail_count, col_num, data)
                    merge_count += 1
                    # 清除buffer，防错
                    buffer_0 = []
                    buffer_1 = []
                else:
                    error_count += 1
                    print('[ERROR]此条交易流水号可能不完整，请根据时间戳人工检查：' + buffer_1['time_stamp'])
        return


# 逐行读取
def read_lines(file):
    with open(file, 'r', encoding='UTF-8') as log_file:
        for line in log_file:
            check_keywords(line)


def get_file_list(file_path):
    file = []
    pattern = 'log'
    for root, dirs, files in os.walk(file_path):
        for f in files:
            searcher = re.search(pattern, f)
            if searcher:
                # 获取文件路径，建立文件列表
                file.append(os.path.join(root, f))
    return file


# 载入界面
print("==================== 中交资管日志分析工具 v1.1.2 ====================\n")
# file_path = "D:\\Users\\forxy\\Documents\\工作内容\\2020\!!! 日志分析\\5月7号门架交易数据\\10.94.217.202\\"
# 用户输入日志文件夹路径
while input_check:
    file_path = input("[INPUT]请输入日志文件夹路径：")
    file = get_file_list(file_path)
    if len(file) == 0:
        print("[ERROR]路径不存在或文件夹为空，请检查后重新输入")
    else:
        print("[INFO]读取文件成功！")
        input_check = False
input_check = True

# 询问是否保存，若为Y或y，将save_flag置于True
while input_check:
    save_chs = input('[INPUT]是否保存*.xlsx结构化数据文件？(y/n)') or 'n'
    if save_chs == 'y' or save_chs == 'Y':
        save_flag = True
        # 退出输入检查循环
        input_check = False
        savefile_name = input('[INPUT]进入结果输出模式，请输入保存文件名：')
        if savefile_name == '':
            print("[ERROR]文件名不能为空，请检查后重新输入")
            input_check = True
        # 建立xlsx文件及worksheet
        workbook = xlsxwriter.Workbook(file_path + '\\' + savefile_name + '.xlsx')
        worksheet_0 = workbook.add_worksheet('统计结果')
        worksheet_1 = workbook.add_worksheet('有效ETC交易')
        worksheet_2 = workbook.add_worksheet('ETC交易特情')
        worksheet_3 = workbook.add_worksheet('有效CPC交易')
        worksheet_4 = workbook.add_worksheet('CPC交易特情')
    elif save_chs == 'n' or save_chs == 'N':
        save_flag = False
        print('[INFO]进入统计检查模式，将不保存结果文件')
        print('\n------------------------------日志载入中----------------------------\n')
        input_check = False
    else:
        print("[ERROR]选项非法，请检查后重新输入")
        input_check = True
input_check = True

# 开始计时器
start_time = datetime.datetime.now()

# 编历文件夹下全部日志
for i in range(len(file)):
    print('[INFO]载入日志文件: ' + file[i])
    read_lines(file[i])

# 结果输出
print('\n-----------------------------交易统计结果---------------------------\n')
# 输出基础交易信息
print('检测到交易数量：' + str(case_count), end='  ')
print('ETC交易数量：' + str(etc_count), end='  ')
print('CPC交易数量：' + str(cpc_count), end='\n')

# 输出ETC流水信息
print('ETC交易应收金额：' + str(etc_aamount_count / 100), end='  ')
print('ETC交易优惠金额：' + str(etc_damount_count / 100), end='  ')
print('ETC交易金额：' + str(etc_tamount_count / 100), end='\n')

# 输出CPC流水信息
print('CPC交易应收金额：' + str(cpc_aamount_count / 100), end='  ')
print('CPC交易优惠金额：' + str(cpc_damount_count / 100), end='  ')
print('CPC交易金额：' + str(cpc_tamount_count / 100))

# 输出总交易流水信息
print('总交易应收金额：' + str((etc_aamount_count + cpc_aamount_count) / 100), end='  ')
print('总交易优惠金额：' + str((etc_damount_count + cpc_damount_count) / 100), end='  ')
print('总交易金额：' + str((etc_tamount_count + cpc_tamount_count) / 100))

print('\n-----------------------------运行统计结果---------------------------\n')
if etc_count > 0:
    print('ETC成功交易数：' + str(etc_suc_count), end='  ')
    print('ETC交易特情数：' + str(etc_fail_count), end='  ')
    print('ETC应排除特情数（分子）：' + str(etc_except_count_u), end='  ')
    print('ETC应排除特情数（分母）：' + str(etc_except_count_d), end='\n')
    etc_suc_percent = round((etc_count - etc_except_count_u)/(etc_count - etc_except_count_d)*100, 2)
    print('ETC交易成功率：' + str(etc_suc_percent) + '%', end='\n\n')

if cpc_count > 0:
    print('CPC成功交易数：' + str(cpc_suc_count), end='  ')
    print('CPC交易特情数：' + str(cpc_fail_count), end='  ')
    print('CPC应排除特情数（分子）：' + str(cpc_except_count_u), end='  ')
    print('CPC应排除特情数（分母）：' + str(cpc_except_count_d), end='\n')
    cpc_suc_percent = round((cpc_count - cpc_except_count_u)/(cpc_count - cpc_except_count_d)*100, 2)
    print('CPC交易成功率：' + str(cpc_suc_percent) + '%', end='\n\n')

if case_count > 0:
    print('总触发交易数：' + str(case_count), end='  ')
    print('总交易特情数：' + str(etc_fail_count + cpc_fail_count), end='  ')
    print('总应排除特情数（分子）：' + str(etc_except_count_u + cpc_except_count_u), end='  ')
    print('总应排除特情数（分母）：' + str(etc_except_count_d + cpc_except_count_d), end='\n')
    suc_percent = round((case_count - etc_except_count_u - cpc_except_count_u)/(case_count - etc_except_count_d - cpc_except_count_d)*100, 2)
    print('总交易成功率：' + str(suc_percent) + '%', end='\n\n')

if error_count > 0:
    print('出现' + str(error_count) + '个特例，请根据处理记录手动处理')
if (error_count / case_count) > 0.005:
    print('门架流水异常率大于0.5%，建议检查门架运行状态')

print('\n-----------------------------车型统计结果---------------------------\n')
print('一型客车：' + str(car_count[1]) + '  二型客车：' + str(car_count[2]) + '  三型客车：' + str(car_count[3]) + '  四型客车：' + str(car_count[4]))
print('一型货车：' + str(truck_count[0]) + '  二型货车：' + str(truck_count[1]) + '  三型货车：' + str(truck_count[2]) + '  四型货车：' + str(truck_count[3]) + '  五型货车：' + str(truck_count[4]) + '  六型货车：' + str(truck_count[5]))
print('一型专项作业车：' + str(spec_vech_count[0]) + '  二型专项作业车：' + str(spec_vech_count[1]) + '  三型专项作业车：' + str(spec_vech_count[2]) + '  四型专项作业车：' + str(spec_vech_count[3]) + '  五型专项作业车：' + str(spec_vech_count[4]) + '  六型专项作业车：' + str(spec_vech_count[5]))
print('无法识别车型：' + str(car_count[0]) + '  特殊识别编号：' + str(truck_count[6]))

if save_flag:
    save_stats_result()
    workbook.close()

# 结束计时器
end_time = datetime.datetime.now()
print('\n-----------------------------程序执行情况---------------------------\n')
print('程序执行及保存用时：', round((end_time - start_time).seconds + (end_time - start_time).microseconds/1000000, 3), 's')

if save_flag:
    print('[INFO]保存数据结果至' + file_path + '\\' + savefile_name + '.xls')
else:
    print('本次为统计检查模式，未进行数据结果导出')
print('\n============================== by ZXY ==============================')
input("按任意键退出..")