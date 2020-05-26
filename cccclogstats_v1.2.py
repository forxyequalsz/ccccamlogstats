import re

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
# 初始化存储用的标题行
save_title = ['时间戳', '日志类型', '日志号', '天线编号', 'MAC地址', '流水号', 'PASSID', '软件版本', '交易类型', '车牌号', '车型',
              '交易状态', '交易状态', '应收金额', '优惠金额', '交易金额', '实际扣款']


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
        print('[ERROR]遇到无法匹配的特殊语句，请手动处理：\n' + line)
        return matcher


# 匹配'车牌号'函数
# 终于优化成一个表达式了
def extract_keyword_2(line):
    pattern = '(?P<time_stamp>[\d\:\.]*)\s' \
              '\[(?P<case_type>[^\s]*)\]\s' \
              '\[(?P<number>[^\s]*)\]\s' \
              '\[(?P<antenna>[^\s]*)\]' \
              '\[(?P<sw_version>[^\s]*)\]' \
              '\*(?P<trade_type>[^\s]*)\s' \
              'MAC:(?P<mac_address>[^\s]*)\s' \
              '车牌号:(?P<plate_no>[^\t]*)\s' \
              '车型:(?P<vech_no>[^\s]*)\s' \
              '(?P<trade_info_1>[交易成功|标签交易成功|交易失败]*)' \
              '[\s]*(?P<trade_info_2>[复合交易失败]*)\s' \
              '[交易特情:]*(?P<spec_info>[|\d]*)\s*'
    regex = re.compile(pattern)
    matcher = regex.match(line)

    if matcher:
        # 若匹配成功，返回dict给check_keywords
        return matcher.groupdict()
    else:
        # 如果没匹配上，报错，返回一个为None的matcher给check_keywords
        print('[ERROR]遇到无法匹配的特殊语句，请手动处理：\n' + line)
        return matcher


def check_keywords(line):
    # 声明全局计数
    global case_count

    # 根据关键词分类处理
    pattern = '流水数据|车牌号:'
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
        # 如果两个buffer均不为空
        if buffer_0 is not None and buffer_1 is not None:
            # 且如果两个buffer里确实有内容（报错整怕了）
            if len(buffer_0) > 0 and len(buffer_1) > 0:
                # 若mac_address可匹配
                if buffer_0['mac_address'] == buffer_1['mac_address']:
                    # 合并到buffer_0
                    buffer_0.update(buffer_1)
                    # 若在存储模式下
                    if save_flag is True:
                        save_list = list(buffer_0.values())
                        for col_num, data in enumerate(save_list):
                            worksheet_1.write(0, col_num, save_title[col_num])
                            worksheet_1.write(etc_suc_count, col_num, data)

# 逐行读取函数
def read_lines(file):
    with open(file, 'r', encoding='UTF-8') as log_file:
        for line in log_file:
            check_keywords(line)