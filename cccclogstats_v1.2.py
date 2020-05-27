import os
import re
import datetime
import xlsxwriter

# 初始化总数计数器
case_count = 0
error_count = 0
count_excp = 0
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
buffer_0 = {}
buffer_1 = {}
merge_count = 0
# 初始化存储类型变量
# 0为etc成功，1为etc失败，2为cpc成功，3为cpc失败
save_flag = False
save_type = 0
# 初始化输入检查器，True为继续检查，False为检查通过
input_check = True
# 初始化存储用的标题行
save_title = ['时间戳', '日志类型', '日志号', '天线编号', 'MAC地址', '流水号', 'PASSID', '软件版本', '交易类型', '车牌号', '车型',
              '交易状态', '交易状态', '应收金额', '优惠金额', '交易金额', '实际扣款', '交易特情']


# 匹配'流水号'函数
# ETC和CPC的字段结构较为统一
def extract_keyword_1(line):
    pattern = '(?P<time_stamp>[\d\:\.]+)\s' \
              '(?:\[(?P<case_type>[^\[\]]+)\])\s' \
              '(?:\[(?P<number>[^\[\]]+)\])\s' \
              '(?:\[(?P<antenna_no>[^\[\]]+)\])' \
              '(?:\[(?P<mac_address>[^\[\]]{8,})\])' \
              '(?:\[(?P<serial_number>[^\[\]]{35,})\])' \
              '[^s]*PASSID:(?P<pass_id>[\w]{36,}),*'
    regex = re.compile(pattern)
    matcher = regex.match(line)
    if matcher:
        # 若匹配成功，返回dict给check_keywords
        return matcher.groupdict()
    else:
        # 如果没匹配上，报错，返回一个为None的matcher给check_keywords
        print('\n[ERROR]遇到无法匹配的特殊语句，请手动处理：\n' + line)
        return matcher


# 剔除不统计的特情
def amount_counter_excp(matcher):
    # 声明全局变量
    global etc_except_count_u
    global etc_except_count_d
    global cpc_except_count_u
    global cpc_except_count_d

    # 从matcher里取交易类型和特情号
    case_type = matcher['trade_type']
    spec_info = matcher['spec_info']

    # 匹配正则表达式
    pattern_u = '145|146|147|148|149|150|151|152|153|154|155|156|157|158|159|160|161|162|163|164|165|166|167|168|169|170|' \
              '171|172|173|174|175|176|177|178|179|180|181|182|183|184|186|189|191|192|193|199'
    pattern_d = '154|186|189|193'
    regex_u = re.compile(pattern_u)
    matcher_u = regex_u.findall(spec_info)
    regex_d = re.compile(pattern_d)
    matcher_d = regex_d.findall(spec_info)

    # 若能匹配
    if matcher_u:
        if case_type == 'ETC':
            etc_except_count_u += 1
        elif case_type == 'CPC':
            cpc_except_count_u += 1
    if matcher_d:
        if case_type == 'ETC':
            etc_except_count_d += 1
        elif case_type == 'CPC':
            cpc_except_count_d += 1
    return


# 交易情况和金额统计函数
def amount_counter(matcher):
    # 声明全局变量
    # 统计例外（万一既没有交易成功也没有交易失败）
    global count_excp
    # ETC运行统计值
    global etc_count
    global etc_suc_count
    global etc_fail_count
    # ETC金额统计值
    global etc_aamount_count
    global etc_damount_count
    global etc_tamount_count
    # CPC运行统计值
    global cpc_count
    global cpc_suc_count
    global cpc_fail_count
    # CPC金额统计值
    global cpc_aamount_count
    global cpc_damount_count
    global cpc_tamount_count

    # 取交易类型和交易成功信息
    case_type = matcher['trade_type']
    trade_info_1 = matcher['trade_info_1']
    trade_info_2 = matcher['trade_info_2']
    # 取交易金额信息
    if matcher['able_amount'] == '':
        aa_amount = 0
    else:
        aa_amount = int(matcher['able_amount'])
    if matcher['disc_amount'] == '':
        da_amount = 0
    else:
        da_amount = int(matcher['disc_amount'])
    if matcher['trade_amount'] == '':
        ta_amount = 0
    else:
        ta_amount = int(matcher['trade_amount'])

    # 先类型判断，后成功失败判断
    if case_type == 'ETC':
        etc_count += 1
        # 算钱
        etc_aamount_count = etc_aamount_count + aa_amount
        etc_damount_count = etc_damount_count + da_amount
        etc_tamount_count = etc_tamount_count + ta_amount
        if trade_info_1 == '交易失败' or trade_info_2 == '复合交易失败':
            etc_fail_count += 1
            # 调用排除特情函数
            amount_counter_excp(matcher)
        else:
            etc_suc_count += 1
    elif case_type == 'CPC':
        cpc_count += 1
        # 算钱
        cpc_aamount_count = cpc_aamount_count + aa_amount
        cpc_damount_count = cpc_damount_count + da_amount
        cpc_tamount_count = cpc_tamount_count + ta_amount
        if trade_info_1 == '交易失败':
            cpc_fail_count += 1
            # 调用排除特情函数
            amount_counter_excp(matcher)
        else:
            cpc_suc_count += 1
    else:
        count_excp += 1
    return


# 车型统计函数
def vechtype_counter(matcher):
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

    vech_type = int(matcher['vech_no'])
    if matcher['able_amount'] != '' and matcher['disc_amount'] != '' and matcher['trade_amount'] != '':
        able_amount = int(matcher['able_amount'])
        disc_amount = int(matcher['disc_amount'])
        trans_amount = int(matcher['trade_amount'])
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


# 匹配'车牌号'函数
# 终于优化成一个表达式了
def extract_keyword_2(line):
    # 声明计数用全局变量
    global error_count
    global count_excp
    # 进行正则表达式匹配
    # 如果还出错就把车牌号里的[^\t]（接受所有非制表符）改成[\w]吧……只是手动处理的量会增加
    pattern = '(?P<time_stamp>[\d\:\.]*)\s' \
              '\[(?P<case_type>[\w]*)\]\s' \
              '\[(?P<number>[\d\w\]*)\]\s' \
              '\[(?P<antenna>[\d\w]*)\]' \
              '\[(?P<sw_version>[.\d\w]*)\]' \
              '\*(?P<trade_type>[\w]*)\s' \
              'MAC:(?P<mac_address>[\w]*)\s' \
              '车牌号:(?P<plate_no>[^\t]*)\s' \
              '车型:(?P<vech_no>[\d]*)\s' \
              '(?P<trade_info_1>[交易成功|标签交易成功|交易失败]*)' \
              '[\s]*(?P<trade_info_2>[复合交易成功|复合交易失败]*)\s' \
              '[\s]*[应收金额:]*(?P<able_amount>[-\d]*)' \
              '[\s]*[优惠金额:]*(?P<disc_amount>[-\d]*)' \
              '[\s]*[交易金额:]*(?P<trade_amount>[-\d]*)' \
              '[\s]*[实际扣款:]*(?P<fact_amount>[-|\d]*)' \
              '[\s]*[交易特情:]*(?P<spec_info>[|\d]*)\s*'
    regex = re.compile(pattern)
    matcher = regex.match(line)
    # 若可匹配
    try:
        matcher.groupdict()
    # 若匹配失败
    except Exception:
        # 错误计数器与统计例外计数器+1
        error_count += 1
        count_excp += 1
        # 显示问题语句，并返回一个为None的matcher给check_keywords
        print('\n[INFO]语句异常，请手动处理:\n' + line)
        return matcher
    else:
        # 调用金额统计函数，存储于全局变量，无需返回值
        amount_counter(matcher)
        # 调用车型统计函数，存储于全局变量，无需返回值
        vechtype_counter(matcher)
        # 返回dict给check_keywords
        return matcher.groupdict()


# 预处理函数
# 如果有'流水数据'和'车牌号'关键字就进入处理流程，否则直接跳过
def check_keywords(line):
    # 声明全局变量
    global buffer_0
    global buffer_1
    global case_count
    global error_count
    global merge_count

    # 根据关键词分类处理
    pattern = '流水数据|车牌号:|不完整的流水'
    searcher = re.search(pattern, line)
    # 如果搜索到关键词
    if searcher:
        # 关键词1返回给buffer_0
        if searcher.group() == '流水数据':
            buffer_0 = extract_keyword_1(line)
        # 关键词2返回给buffer_1
        elif searcher.group() == '车牌号:':
            case_count += 1
            buffer_1 = extract_keyword_2(line)
        elif searcher.group() == '不完整的流水':
            error_count += 1
        # extract_keyword函数返回的结果有两种，一种是匹配到后的dict，一种是匹配失败的None
        # 拦截匹配异常语句
        if buffer_0 is not None and buffer_1 is not None:
            # 如果均有结果
            if len(buffer_0) > 0 and len(buffer_1) > 0:
                # 若mac_address可匹配
                if buffer_0['mac_address'] == buffer_1['mac_address']:
                    # 合并到buffer_0
                    buffer_0.update(buffer_1)
                    merge_count += 1
                    # 若在存储模式下
                    if save_flag is True:
                        save_list = list(buffer_0.values())
                        # 笨办法写了……13到16是金额，写入时候用数字格式
                        for col_num, data in enumerate(save_list):
                            worksheet_2.write(0, col_num, save_title[col_num])
                            if col_num < 13 or col_num >16:
                                worksheet_2.write(case_count, col_num, data)
                            elif col_num > 12 and col_num < 17:
                                if data == '':
                                    data = 0
                                worksheet_2.write_number(case_count, col_num, int(data))
                    # 清除buffer，防错
                    buffer_0 = []
                    buffer_1 = []
                else:
                    print('\n[ERROR]此条交易流水号可能不完整，请根据时间戳复核：' + buffer_1['time_stamp'], end='')


# 逐行读取函数
def read_lines(file):
    with open(file, 'r', encoding='UTF-8') as log_file:
        for line in log_file:
            check_keywords(line)


# 读取文件列表函数
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


# 结果输出函数
def print_out():
    print('\n====================         运行统计结果     ====================\n')
    # 输出基础交易信息
    print('检测到总交易事件：' + str(case_count), end='\n')
    # 输出ETC交易信息
    print('- ETC交易事件：' + str(etc_count), end='\n')
    print('-- ETC交易成功数：' + str(etc_suc_count), end='  ')
    print('ETC交易特情数：' + str(etc_fail_count), end='\n')
    if etc_count > 0:
        print('-- ETC应排除特情数（分子）：' + str(etc_except_count_u), end='  ')
        print('ETC应排除特情数（分母）：' + str(etc_except_count_d), end='\n')
        etc_suc_percent = round((etc_count - etc_except_count_u)/(etc_count - etc_except_count_d)*100, 2)
        print('ETC交易成功率：' + str(etc_suc_percent) + '%', end='\n\n')
    # 输出CPC交易信息
    print('-CPC交易事件：' + str(cpc_count), end='\n')
    print('-- CPC交易成功数：' + str(cpc_suc_count), end='  ')
    print('CPC交易特情数：' + str(cpc_fail_count), end='\n')
    if cpc_count > 0:
        print('-- CPC应排除特情数（分子）：' + str(cpc_except_count_u), end='  ')
        print('CPC应排除特情数（分母）：' + str(cpc_except_count_d), end='\n')
        cpc_suc_percent = round((cpc_count - cpc_except_count_u)/(cpc_count - cpc_except_count_d)*100, 2)
        print('CPC交易成功率：' + str(cpc_suc_percent) + '%', end='\n\n')
    # 输出总统计信息
    if case_count > 0:
        print('总交易特情数：' + str(etc_fail_count + cpc_fail_count), end='\n')
        print('总应排除特情数（分子）：' + str(etc_except_count_u + cpc_except_count_u), end='  ')
        print('总应排除特情数（分母）：' + str(etc_except_count_d + cpc_except_count_d), end='\n')
        suc_percent = round((case_count - etc_except_count_u - cpc_except_count_u)/(case_count - etc_except_count_d - cpc_except_count_d)*100, 2)
        print('总交易成功率：' + str(suc_percent) + '%', end='\n\n')
    # 输出异常结果
    if error_count > 0:
        print('出现' + str(error_count) + '个异常结果，请根据处理记录手动复核')
        if (error_count / case_count) > 0.005:
            print('门架流水异常率大于0.5%，建议检查门架运行状态')

    print('\n====================         金额统计结果     ====================\n')
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
    print('(单位：元)')

    print('\n====================         车型统计结果     ====================\n')
    print('一型客车：' + str(car_count[1]) + '  二型客车：' + str(car_count[2]) + '  三型客车：' + str(car_count[3]) + '  四型客车：' + str(car_count[4]))
    print('一型货车：' + str(truck_count[0]) + '  二型货车：' + str(truck_count[1]) + '  三型货车：' + str(truck_count[2]) + '  四型货车：' + str(truck_count[3]) + '  五型货车：' + str(truck_count[4]) + '  六型货车：' + str(truck_count[5]))
    print('一型专项作业车：' + str(spec_vech_count[0]) + '  二型专项作业车：' + str(spec_vech_count[1]) + '  三型专项作业车：' + str(spec_vech_count[2]) + '  四型专项作业车：' + str(spec_vech_count[3]) + '  五型专项作业车：' + str(spec_vech_count[4]) + '  六型专项作业车：' + str(spec_vech_count[5]))
    print('特殊识别编号：' + str(truck_count[6]) + '  无法识别车型：' + str(car_count[0]) + '  异常数据：' + str(count_excp))


# 保存车型统计结果
def save_vech_result():
    # 先写表头
    title_column = ['一型客车', '二型客车', '三型客车', '四型客车', '一型货车', '二型货车', '三型货车', '四型货车','五型货车',
                   '六型货车', '一型专项作业车', '二型专项作业车', '三型专项作业车', '四型专项作业车', '五型专项作业车',
                   '六型专项作业车', '无法识别车型', '特殊识别编号']
    title_row = ['数量', '应收金额（元）', '折扣金额（元）', '交易金额（元）']
    worksheet_1.write_column('A2', title_column)
    worksheet_1.write_row('B1', title_row)
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
    worksheet_1.set_column('A:E', 20)
    # 写入统计结果
    worksheet_1.write_column('B2', count_list)
    worksheet_1.write_column('C2', aa_list)
    worksheet_1.write_column('D2', da_list)
    worksheet_1.write_column('E2', ta_list)
    return


# 主功能程序（写的挺杂的，懒得另起那么多函数了）
# 载入界面
print("====================  中交资管日志分析工具  v1.2  =====================\n")
# 用户输入日志文件夹路径
while input_check:
    file_path = input("[INPUT]请输入日志文件夹路径：")
    file = get_file_list(file_path)
    if len(file) == 0:
        print("[ERROR]路径不存在或文件夹为空，请检查后重新输入")
    else:
        print('[INFO]检测到日志文件' + str(len(file)) + '个')
        input_check = False
input_check = True

# 询问是否保存，若为Y或y，将save_flag置于True
while input_check:
    save_chs = input('[INPUT]是否保存xlsx格式统计结果及数据文件？(y/n)') or 'n'
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
        # 暂时没提金额统计的需求，先不写了
        # worksheet_0 = workbook.add_worksheet('金额统计')
        worksheet_1 = workbook.add_worksheet('车型统计')
        worksheet_2 = workbook.add_worksheet('原始数据')
    elif save_chs == 'n' or save_chs == 'N':
        save_flag = False
        print('[INFO]进入统计检查模式，将不保存结果文件')
        print('\n====================         日志文件读取     ====================\n')
        input_check = False
    else:
        print("[ERROR]选项非法，请检查后重新输入")
        input_check = True
input_check = True

# 开始计时器
start_time = datetime.datetime.now()

# 编历文件夹下全部日志
for i in range(len(file)):
    print('[INFO]载入日志文件:' + file[i])
    read_lines(file[i])
print('\n[INFO]日志已全部加载完毕！')

# 打印统计结果
print_out()

# 若为保存模式，保存
if save_flag:
    save_vech_result()
    workbook.close()

# 结束计时器
end_time = datetime.datetime.now()
print('\n====================         程序执行结果     ====================\n')
print('程序执行及保存用时：', round((end_time - start_time).seconds + (end_time - start_time).microseconds/1000000, 3), 's')
if save_flag:
    print('[INFO]保存数据结果至' + file_path + '\\' + savefile_name + '.xls')
else:
    print('本次为统计检查模式，未进行数据结果导出')
print('\n====================       By ZXY       ====================')
input("按任意键退出..")