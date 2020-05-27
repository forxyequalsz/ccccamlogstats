import re
import os

suc_counter = 0
fail_counter = 0
money_counter = 0

def check_keywords(line):
    pattern = '车牌号:'
    searcher = re.search(pattern, line)
    if searcher:
        read_lines(line)
    return


def read_lines(line):
    global suc_counter
    global fail_counter
    global money_counter

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

    try:
        checker = matcher.groupdict()
        ck1 = checker['able_amount']
        ck2 = checker['trade_info_1']
        if ck1 != '':
            money_counter = money_counter + int(ck1)
        # print(matcher.groupdict())
        if ck2 != '交易失败' and ck1 == '':
            print('检查可疑语句：\n' + line)
        suc_counter += 1
    except Exception:
        print('\n[INFO]语句异常，请手动处理:\n' + line)
        fail_counter += 1
    return


file_path = input('请输入路径：')
file = []
pattern = 'log'
for root, dirs, files in os.walk(file_path):
    for f in files:
        searcher = re.search(pattern, f)
        if searcher:
            # 获取文件路径，建立文件列表
            file.append(os.path.join(root, f))
print('[INFO]检测到日志文件' + str(len(file)) + '个，读取中…')

for i in range(len(file)):
    print('\r[INFO]载入日志文件:' + file[i], end='')
    with open(file[i], 'r', encoding='UTF-8') as log_file:
        for line in log_file:
            check_keywords(line)

print('\n分离成功语句' + str(suc_counter) + '条')
print('检测到异常语句' + str(fail_counter) + '条')
print('合计金额：' + str(money_counter/100) + '元')