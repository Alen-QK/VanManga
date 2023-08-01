import re


def chapter_title_reformat(chapterTitle):
    # 正则表达式，用于分离所有s或S后紧跟任意数字的情况
    pattern = re.compile(r'(s|S)[0-9]+')

    # 每次只匹配当前title中第一个符合正则的子串，直到title中不再存在任何符合正则的情况
    while pattern.search(chapterTitle):
        match = pattern.search(chapterTitle)
        # 获取子串的开始位置
        startIdx = match.span()[0] # startIdx是s/S的位置
        # 前后分离title
        prevStr = chapterTitle[:startIdx + 1] # 因为是从s/S数字之后开始添加#，所以前面的部分要包含s/S，故取到startIdx + 1
        nextStr = chapterTitle[startIdx + 1:] # 把s/S后面的子串分离出来
        chapterTitle = prevStr + '#' + nextStr

    chapterTitle = chapterTitle.replace('-', '#')
    chapterTitle = chapterTitle.replace('(', '（').replace(')', '）')

    return chapterTitle

# test cases
# word = ['电锯人s1s0s10086', '电(锯)人S100086', '电(-)锯人s010010', '电锯人s1', '电锯人s0', '电锯人s080018', '-电(s11)锯s0人S2', '电s11锯s0人S2', '电锯人第100话sAAA']
# #
# for w in word:
#     print(chapter_title_reformat(w))